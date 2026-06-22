"""TrendFollowingStrategy — reward clean, stable upward trends."""
from __future__ import annotations

from typing import Any, Dict, List

from strategy.base import NEGATIVE, NEUTRAL, POSITIVE, StrategyPlugin, StrategyResult, map_linear
from utils import clamp


class TrendFollowingStrategy(StrategyPlugin):
    def name(self) -> str:
        return "trend_following"

    def describe(self) -> str:
        return "Identifies stocks in a clean, stable, upward trend using the available price series."

    def required_fields(self) -> List[str]:
        return ["graph"]

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        prices = self._prices(market_data)
        change_pct = market_data.get("change_pct")
        warnings: List[str] = []

        if len(prices) >= 2 and prices[0]:
            trend_pct = (prices[-1] - prices[0]) / prices[0] * 100.0
            # Smoothness: penalize a choppy series even if net direction is up.
            ups = sum(1 for a, b in zip(prices, prices[1:]) if b >= a)
            smoothness = ups / max(1, len(prices) - 1)
            confidence = clamp(0.4 + len(prices) / 60.0, 0.4, 0.85)
        elif change_pct is not None:
            trend_pct = change_pct
            smoothness = 0.5
            confidence = 0.3
            warnings.append("No multi-point series; using today's move as a trend proxy.")
        else:
            return StrategyResult(self.name(), 50.0, 0.1, NEUTRAL,
                                  "No price series available to assess trend.",
                                  warnings=["missing_graph"], is_valid=False)

        base = map_linear(trend_pct, -5.0, 5.0)
        # Blend in smoothness (a stable uptrend scores higher than a jagged one).
        score = clamp(base * (0.7 + 0.3 * smoothness), 0.0, 100.0)
        signal = POSITIVE if score >= 60 else NEGATIVE if score <= 40 else NEUTRAL
        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=round(confidence, 2),
            signal=signal,
            reason=f"Trend {trend_pct:+.2f}% over {len(prices)} points, smoothness {smoothness:.0%}.",
            data_used={"trend_pct": round(trend_pct, 3), "points": len(prices), "smoothness": round(smoothness, 2)},
            warnings=warnings,
        )
