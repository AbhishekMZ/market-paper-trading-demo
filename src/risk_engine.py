"""Risk engine — the primary safety gate.

Enforces every hard rule before an order may be built/placed, and produces
loss-review labels for open positions. It NEVER auto-sells; loss reviews are
advisory (the system prefers explicit, explainable action).

All decisions return a RiskDecision with the exact rules checked/failed so the
audit log and reports can explain *why*.
"""
from __future__ import annotations

from typing import Any, Dict, List

from order_models import DataQuality, RiskDecision, RiskLevel, SignalLabel, TradeSignal


class RiskEngine:
    def __init__(self, risk_cfg: Dict[str, Any]) -> None:
        r = risk_cfg.get("risk", risk_cfg)
        self.max_trade_amount = float(r.get("max_trade_amount", 2000))
        self.monthly_cap = float(r.get("monthly_capital_cap", 10000))
        self.max_buys_per_day = int(r.get("max_buys_per_day", 1))
        self.max_buys_per_month = int(r.get("max_buys_per_month", 5))
        self.max_alloc_pct = float(r.get("max_position_allocation_pct", 25))
        self.allowed_products = set(r.get("allowed_product_types", ["DELIVERY"]))
        self.allowed_order_types = set(r.get("allowed_order_types", ["LIMIT"]))
        self.sell_scope = r.get("sell_scope", "bot_owned_only")
        self.reject_on_stale = bool(r.get("reject_on_stale_data", True))
        self.allow_real_orders = bool(r.get("allow_real_orders", False))
        self.thresholds = r.get("loss_review_thresholds", {})

    # ------------------------------------------------------------------ #
    # Buy gate
    # ------------------------------------------------------------------ #
    def evaluate_buy(
        self,
        signal: TradeSignal,
        amount: float,
        portfolio: Dict[str, Any],
        buys_today: int,
        buys_this_month: int,
        capital_deployed_this_month: float,
        is_paper: bool = True,
    ) -> RiskDecision:
        checked: List[str] = []
        failed: List[str] = []

        def check(name: str, ok: bool) -> None:
            checked.append(name)
            if not ok:
                failed.append(name)

        # Hard v1 block: no real orders. A non-paper order is only allowed if
        # real orders are explicitly enabled (never the case in v1).
        check("real_orders_blocked_in_v1", is_paper or self.allow_real_orders)

        # Data quality / staleness.
        check(
            "data_quality_acceptable",
            signal.data_quality in (DataQuality.GOOD, DataQuality.ACCEPTABLE),
        )
        # Risk level not HIGH.
        check("risk_level_not_high", signal.risk_level != RiskLevel.HIGH)
        # Per-trade cap.
        check("max_per_trade", amount <= self.max_trade_amount + 1e-6)
        # Monthly capital remaining.
        remaining = self.monthly_cap - capital_deployed_this_month
        check("monthly_capital_remaining", amount <= remaining + 1e-6)
        # Daily buy count.
        check("daily_buy_limit", buys_today < self.max_buys_per_day)
        # Monthly buy count.
        check("monthly_buy_limit", buys_this_month < self.max_buys_per_month)
        # Over-allocation to a single name.
        existing_alloc = self._existing_allocation(portfolio, signal.symbol)
        max_alloc_value = self.monthly_cap * self.max_alloc_pct / 100.0
        check("position_allocation_cap", existing_alloc + amount <= max_alloc_value + 1e-6)

        approved = len(failed) == 0
        reason = (
            f"BUY approved for {signal.symbol}: passed {len(checked)} risk checks."
            if approved
            else f"BUY rejected for {signal.symbol}: failed {failed}."
        )
        return RiskDecision(
            approved=approved,
            symbol=signal.symbol,
            reason=reason,
            rules_checked=checked,
            rules_failed=failed,
            risk_level=signal.risk_level,
        )

    # ------------------------------------------------------------------ #
    # Sell gate
    # ------------------------------------------------------------------ #
    def evaluate_sell(
        self, symbol: str, quantity: int, portfolio: Dict[str, Any], is_paper: bool = True
    ) -> RiskDecision:
        checked: List[str] = []
        failed: List[str] = []
        pos = next((p for p in portfolio.get("positions", []) if p["symbol"] == symbol), None)

        checked.append("real_orders_blocked_in_v1")
        if not is_paper and not self.allow_real_orders:
            failed.append("real_orders_blocked_in_v1")

        checked.append("sell_scope_bot_owned_only")
        if pos is None or not pos.get("bot_owned", False):
            failed.append("sell_scope_bot_owned_only")

        checked.append("sell_qty_available")
        if pos is None or quantity > pos.get("quantity", 0):
            failed.append("sell_qty_available")

        approved = len(failed) == 0
        reason = (
            f"SELL approved for {symbol}."
            if approved
            else f"SELL rejected for {symbol}: failed {failed}."
        )
        return RiskDecision(
            approved=approved,
            symbol=symbol,
            reason=reason,
            rules_checked=checked,
            rules_failed=failed,
        )

    # ------------------------------------------------------------------ #
    # Loss reviews (advisory — never auto-sell)
    # ------------------------------------------------------------------ #
    def review_positions(self, portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
        soft = float(self.thresholds.get("soft_review_pct", -7))
        strong = float(self.thresholds.get("strong_review_pct", -10))
        hard = float(self.thresholds.get("hard_review_pct", -15))
        reviews: List[Dict[str, Any]] = []
        for p in portfolio.get("positions", []):
            pnl_pct = p.get("unrealized_pnl_pct")
            if pnl_pct is None:
                continue
            if pnl_pct <= hard:
                label, thr = SignalLabel.EXIT_REVIEW, hard
            elif pnl_pct <= strong:
                label, thr = SignalLabel.TRIM_REVIEW, strong
            elif pnl_pct <= soft:
                label, thr = SignalLabel.SELL_REVIEW, soft
            else:
                p["risk_status"] = "OK"
                continue
            p["risk_status"] = label.value
            reviews.append(
                {
                    "symbol": p["symbol"],
                    "unrealized_pnl_pct": pnl_pct,
                    "label": label.value,
                    "threshold_pct": thr,
                    "reason": (
                        f"{p['symbol']} at {pnl_pct:.2f}% breaches the {thr:.0f}% review level. "
                        "No automatic sell — flagged for manual review."
                    ),
                }
            )
        return reviews

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _existing_allocation(portfolio: Dict[str, Any], symbol: str) -> float:
        pos = next((p for p in portfolio.get("positions", []) if p["symbol"] == symbol), None)
        return float(pos.get("invested", 0.0)) if pos else 0.0
