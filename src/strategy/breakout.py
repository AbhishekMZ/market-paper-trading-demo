"""BreakoutStrategy — momentum breakouts with trend confirmation.

EXPERIMENTAL in v1: display-only by default. Requires trend confirmation,
returns neutral on insufficient data, and avoids chasing extreme one-day moves.
"""
from __future__ import annotations

from typing import Any, Dict, List

from strategy.base import NEGATIVE, NEUTRAL, POSITIVE, StrategyPlugin, StrategyResult


class BreakoutStrategy(StrategyPlugin):
    default_contributes_to_score = False

    def name(self) -> str:
        return "breakout"

    def describe(self) -> str:
        return "Flags momentum breakouts near the top of the recent range, confirmed by trend."

    def required_fields(self) -> List[str]:
        return ["graph"]

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        prices = self._prices(market_data)
        change_pct = market_data.get("change_pct")
        warnings: List[str] = []

        if len(prices) < 5:
            return StrategyResult(self.name(), 50.0, 0.15, NEUTRAL,
                                  "Insufficient data for breakout assessment.",
                                  warnings=["insufficient_data"], display_only=True,
                                  contributes_to_score=False)

        hi = max(prices)
        lo = min(prices)
        last = prices[-1]
        rng = hi - lo
        pos_in_range = (last - lo) / rng if rng else 0.0
        trend_up = prices[-1] >= prices[0]

        if change_pct is not None and change_pct >= 5.0:
            score, signal = 45.0, NEUTRAL
            reason = f"Already up {change_pct:.2f}% today — avoid chasing an extended move."
        elif pos_in_range >= 0.9 and trend_up:
            score, signal = 70.0, POSITIVE
            reason = f"Near range high ({pos_in_range:.0%}) with up-trend confirmation — breakout setup."
        elif pos_in_range >= 0.9 and not trend_up:
            score, signal = 50.0, NEUTRAL
            reason = "Near range high but trend not confirmed."
        else:
            score, signal = 48.0, NEUTRAL
            reason = f"No breakout ({pos_in_range:.0%} of range)."

        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=score,
            confidence=0.4,
            signal=signal,
            reason=reason,
            data_used={"pos_in_range": round(pos_in_range, 2), "trend_up": trend_up, "change_pct": change_pct},
            warnings=warnings,
            display_only=True,
            contributes_to_score=False,
        )
