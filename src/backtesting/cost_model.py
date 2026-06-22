"""CostModel — estimated Indian equity DELIVERY transaction costs.

Used to show COST-ADJUSTED paper P&L so the demo does not look unrealistically
profitable. All rates are configurable placeholders (config/costs.yml). This is
an estimate, not a precise broker contract note.
"""
from __future__ import annotations

from typing import Any, Dict


class CostModel:
    def __init__(self, costs_cfg: Dict[str, Any]) -> None:
        c = costs_cfg.get("costs", costs_cfg) if costs_cfg else {}
        self.brokerage_pct = float(c.get("brokerage_pct", 0.0))
        self.brokerage_cap = float(c.get("brokerage_cap", 20.0))
        self.stt_pct = float(c.get("stt_pct", 0.001))
        self.exchange_txn_pct = float(c.get("exchange_txn_pct", 0.0000297))
        self.sebi_pct = float(c.get("sebi_pct", 0.000001))
        self.gst_pct = float(c.get("gst_pct", 0.18))
        self.stamp_duty_pct = float(c.get("stamp_duty_pct", 0.00015))
        self.slippage_pct = float(c.get("slippage_pct", 0.0005))
        self.bid_ask_spread_pct = float(c.get("bid_ask_spread_pct", 0.0003))

    def side_cost(self, amount: float, side: str) -> Dict[str, float]:
        """Estimated cost breakdown for one side (BUY or SELL)."""
        side = side.upper()
        brokerage = min(amount * self.brokerage_pct, self.brokerage_cap) if self.brokerage_pct else 0.0
        stt = amount * self.stt_pct
        exchange = amount * self.exchange_txn_pct
        sebi = amount * self.sebi_pct
        gst = (brokerage + exchange + sebi) * self.gst_pct
        stamp = amount * self.stamp_duty_pct if side == "BUY" else 0.0
        slippage = amount * self.slippage_pct
        spread = amount * self.bid_ask_spread_pct / 2.0
        total = brokerage + stt + exchange + sebi + gst + stamp + slippage + spread
        return {
            "brokerage": round(brokerage, 4),
            "stt": round(stt, 4),
            "exchange_txn": round(exchange, 4),
            "sebi": round(sebi, 4),
            "gst": round(gst, 4),
            "stamp_duty": round(stamp, 4),
            "slippage": round(slippage, 4),
            "bid_ask_spread": round(spread, 4),
            "total": round(total, 2),
        }

    def buy_cost(self, amount: float) -> float:
        return self.side_cost(amount, "BUY")["total"]

    def sell_cost(self, amount: float) -> float:
        return self.side_cost(amount, "SELL")["total"]

    def round_trip_cost(self, amount: float) -> float:
        """Total estimated cost to buy AND later sell roughly `amount` worth."""
        return round(self.buy_cost(amount) + self.sell_cost(amount), 2)

    def breakdown(self, amount: float) -> Dict[str, Any]:
        buy = self.side_cost(amount, "BUY")
        sell = self.side_cost(amount, "SELL")
        return {
            "amount": round(amount, 2),
            "buy": buy,
            "sell": sell,
            "round_trip_total": round(buy["total"] + sell["total"], 2),
            "round_trip_pct": round((buy["total"] + sell["total"]) / amount * 100, 4) if amount else 0.0,
        }
