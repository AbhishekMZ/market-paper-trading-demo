"""RelativeStrengthStrategy — trailing excess return versus the benchmark.

Uses the 60-session excess return from the same trailing series as the
historical-context features. A one-day move is not a relative-strength read.
"""
from __future__ import annotations

from typing import Any, Dict, List

from strategy.base import (
    NEGATIVE,
    NEUTRAL,
    POSITIVE,
    StrategyPlugin,
    StrategyResult,
    map_linear,
    trailing_features,
    unavailable_result,
)


class RelativeStrengthStrategy(StrategyPlugin):
    def name(self) -> str:
        return "relative_strength"

    def describe(self) -> str:
        return "60-session excess return versus the benchmark. One-day moves are not used."

    def required_fields(self) -> List[str]:
        return []

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        feats = trailing_features(context, symbol)
        rel = None if not feats else feats.get("excess_return_60d")
        if rel is None:
            return unavailable_result(
                self.name(),
                "Trailing 60-session excess return unavailable; one-day move is not used.",
            )

        # ±8% over 60 sessions spans a weak to strong excess return.
        score = map_linear(float(rel), -8.0, 8.0)
        signal = POSITIVE if score >= 60 else NEGATIVE if score <= 40 else NEUTRAL
        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=0.7,
            signal=signal,
            reason=f"60-session excess return vs benchmark {float(rel):+.2f}%.",
            data_used={"excess_return_60d": rel, "window_sessions": 60},
        )
