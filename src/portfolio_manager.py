"""Portfolio manager — analytics over the paper portfolio.

Owns mark-to-market valuation and the monthly budget counters. The order
ledger itself (cash, positions, realized P&L) is mutated by PaperBrokerAdapter;
this module reads that ledger, revalues it against current prices, and tracks
budget usage / drawdown.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import storage
from utils import month_ist_str, now_ist_iso


class PortfolioManager:
    def __init__(self, settings: Dict[str, Any]) -> None:
        cap = settings.get("capital", {})
        self.monthly_capital = float(cap.get("monthly_fake_capital", 10000))
        self.max_buys_per_month = int(cap.get("max_buys_per_month", 5))

    # ------------------------------------------------------------------ #
    # Monthly budget
    # ------------------------------------------------------------------ #
    def load_budget(self) -> Dict[str, Any]:
        budget = storage.load_state("monthly_budget", {})
        if not budget or budget.get("month") != month_ist_str():
            budget = {
                "month": month_ist_str(),
                "monthly_capital": self.monthly_capital,
                "capital_deployed": 0.0,
                "capital_remaining": self.monthly_capital,
                "buys_this_month": 0,
                "max_buys_per_month": self.max_buys_per_month,
                "realized_pnl_month": 0.0,
            }
            storage.save_state("monthly_budget", budget)
        else:
            # Keep config-derived caps in sync within the same month, so a
            # mid-month settings change (e.g. raising max_buys_per_month or
            # monthly_capital) is reflected immediately instead of only at the
            # start of the next month. Accumulated counters are preserved.
            changed = False
            if budget.get("max_buys_per_month") != self.max_buys_per_month:
                budget["max_buys_per_month"] = self.max_buys_per_month
                changed = True
            if budget.get("monthly_capital") != self.monthly_capital:
                budget["monthly_capital"] = self.monthly_capital
                budget["capital_remaining"] = round(
                    self.monthly_capital - budget.get("capital_deployed", 0.0), 2
                )
                changed = True
            if changed:
                storage.save_state("monthly_budget", budget)
        return budget

    def record_buy(self, amount: float) -> Dict[str, Any]:
        budget = self.load_budget()
        budget["capital_deployed"] = round(budget.get("capital_deployed", 0.0) + amount, 2)
        budget["capital_remaining"] = round(self.monthly_capital - budget["capital_deployed"], 2)
        budget["buys_this_month"] = int(budget.get("buys_this_month", 0)) + 1
        storage.save_state("monthly_budget", budget)
        return budget

    def record_sell(self, realized_pnl: float) -> Dict[str, Any]:
        budget = self.load_budget()
        budget["realized_pnl_month"] = round(budget.get("realized_pnl_month", 0.0) + realized_pnl, 2)
        storage.save_state("monthly_budget", budget)
        return budget

    # ------------------------------------------------------------------ #
    # Mark-to-market
    # ------------------------------------------------------------------ #
    def mark_to_market(
        self,
        prices: Dict[str, Optional[float]],
        anomalous_symbols: Optional[set] = None,
        mtm_jump_pct: float = 15.0,
    ) -> Dict[str, Any]:
        """Revalue holdings. A new mark that jumps more than mtm_jump_pct vs the
        last-known-good price (or that comes from a DATA_ANOMALY symbol) is
        REJECTED: the prior price is kept and the position flagged, so a bad/
        adjusted quote can never produce a misleading P&L. Returns the portfolio;
        any rejections are recorded in self.last_mtm_incidents.
        """
        anomalous_symbols = anomalous_symbols or set()
        self.last_mtm_incidents: List[Dict[str, Any]] = []
        pf = storage.load_state("portfolio", {})
        if not pf:
            return pf
        holdings_value = 0.0
        unrealized = 0.0
        for p in pf.get("positions", []):
            prev = p.get("last_price", p.get("avg_price"))
            last = prices.get(p["symbol"])
            if last is None:
                last = prev
            last = float(last)
            # Reject anomalous marks: keep the last-known-good price, flag, record.
            jump_pct = abs(last - prev) / prev * 100.0 if prev else 0.0
            if p["symbol"] in anomalous_symbols or jump_pct > mtm_jump_pct:
                self.last_mtm_incidents.append({
                    "ts": now_ist_iso(), "symbol": p["symbol"], "issue": "mtm_price_rejected",
                    "prev_price": prev, "rejected_price": last, "jump_pct": round(jump_pct, 2),
                    "action": "kept_last_known_good_price; flagged DATA_ANOMALY; not traded",
                })
                p["data_status"] = "DATA_ANOMALY"
                p["risk_status"] = "DATA_ANOMALY"
                last = float(prev)  # keep last good
            else:
                p.setdefault("data_status", "OK")
                if p.get("data_status") == "DATA_ANOMALY":
                    p["data_status"] = "OK"
            qty = p["quantity"]
            current_value = round(last * qty, 2)
            invested = p.get("invested", p["avg_price"] * qty)
            p["last_price"] = round(last, 4)
            p["current_value"] = current_value
            p["unrealized_pnl"] = round(current_value - invested, 2)
            p["unrealized_pnl_pct"] = round((last / p["avg_price"] - 1) * 100, 2) if p["avg_price"] else 0.0
            holdings_value += current_value
            unrealized += p["unrealized_pnl"]

        cash = float(pf.get("cash", 0.0))
        total_value = round(cash + holdings_value, 2)
        pf["holdings_value"] = round(holdings_value, 2)
        pf["unrealized_pnl"] = round(unrealized, 2)
        pf["total_value"] = total_value

        # Drawdown tracking.
        peak = float(pf.get("peak_total_value", pf.get("starting_capital", total_value)))
        peak = max(peak, total_value)
        pf["peak_total_value"] = round(peak, 2)
        pf["max_drawdown_pct"] = round((total_value / peak - 1) * 100, 2) if peak else 0.0
        pf["as_of"] = now_ist_iso()
        storage.save_state("portfolio", pf)
        return pf

    # ------------------------------------------------------------------ #
    # Summary for reports / dashboard
    # ------------------------------------------------------------------ #
    def summary(self) -> Dict[str, Any]:
        pf = storage.load_state("portfolio", {})
        budget = self.load_budget()
        starting = float(pf.get("starting_capital", self.monthly_capital))
        total_value = float(pf.get("total_value", starting))
        realized = float(pf.get("realized_pnl", 0.0))
        unrealized = float(pf.get("unrealized_pnl", 0.0))
        positions = pf.get("positions", [])
        closed = pf.get("closed_positions", [])
        return {
            "as_of": pf.get("as_of", now_ist_iso()),
            "starting_capital": starting,
            "cash": float(pf.get("cash", 0.0)),
            "holdings_value": float(pf.get("holdings_value", 0.0)),
            "total_value": total_value,
            "realized_pnl": realized,
            "unrealized_pnl": unrealized,
            "total_pnl": round(realized + unrealized, 2),
            "total_return_pct": round((total_value / starting - 1) * 100, 2) if starting else 0.0,
            "max_drawdown_pct": float(pf.get("max_drawdown_pct", 0.0)),
            "open_positions": len(positions),
            "closed_positions": len(closed),
            "monthly_capital": budget.get("monthly_capital", self.monthly_capital),
            "capital_deployed": budget.get("capital_deployed", 0.0),
            "capital_remaining": budget.get("capital_remaining", self.monthly_capital),
            "buys_this_month": budget.get("buys_this_month", 0),
            "max_buys_per_month": budget.get("max_buys_per_month", self.max_buys_per_month),
            "positions": positions,
            "closed": closed,
        }
