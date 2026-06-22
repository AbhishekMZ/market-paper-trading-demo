"""MeanReversionStrategy — controlled pullbacks only, never falling knives.

EXPERIMENTAL in v1: display-only by default (contributes_to_score=false in
config/scoring.yml). It must be explicitly enabled before it can affect buys.
"""
from __future__ import annotations

import statistics
from typing import Any, Dict, List

from strategy.base import NEGATIVE, NEUTRAL, POSITIVE, StrategyPlugin, StrategyResult


class MeanReversionStrategy(StrategyPlugin):
    default_contributes_to_score = False

    def name(self) -> str:
        return "mean_reversion"

    def describe(self) -> str:
        return "Rewards controlled pullbacks within a healthy trend; penalizes sharp falls / falling knives."

    def required_fields(self) -> List[str]:
        return ["graph", "change_pct"]

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        prices = self._prices(market_data)
        change_pct = market_data.get("change_pct")
        warnings: List[str] = []

        if len(prices) < 4 or change_pct is None:
            return StrategyResult(self.name(), 50.0, 0.15, NEUTRAL,
                                  "Insufficient data for mean-reversion assessment.",
                                  warnings=["insufficient_data"], display_only=True,
                                  contributes_to_score=False)

        mean = statistics.fmean(prices)
        last = prices[-1]
        broader_trend = (prices[-1] - prices[0]) / prices[0] * 100.0 if prices[0] else 0.0
        below_mean_pct = (last - mean) / mean * 100.0 if mean else 0.0

        # A pullback is only constructive when the broader trend is healthy.
        if change_pct <= -4.0:
            score, signal = 25.0, NEGATIVE
            reason = f"Sharp fall {change_pct:.2f}% — treated as risk, not a buyable dip."
        elif broader_trend > 0 and -2.5 <= change_pct <= -0.3 and below_mean_pct < 0:
            score, signal = 68.0, POSITIVE
            reason = f"Controlled pullback ({change_pct:.2f}%) within an up-trend ({broader_trend:+.2f}%)."
        elif broader_trend <= 0:
            score, signal = 40.0, NEGATIVE
            reason = f"Pullback inside a flat/down trend ({broader_trend:+.2f}%) — not constructive."
        else:
            score, signal = 52.0, NEUTRAL
            reason = "No clear mean-reversion setup."

        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=score,
            confidence=0.4,
            signal=signal,
            reason=reason,
            data_used={"broader_trend_pct": round(broader_trend, 2),
                       "below_mean_pct": round(below_mean_pct, 2), "change_pct": change_pct},
            warnings=warnings,
            display_only=True,
            contributes_to_score=False,
        )
