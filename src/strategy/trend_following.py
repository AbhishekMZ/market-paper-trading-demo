"""TrendFollowingStrategy — distance to the trailing moving averages.

Scores pct-above the 50-session average, damped by how persistently price has
stayed above it. The 200-session average, when present, pulls the score back
toward neutral if it disagrees. The 1-month snapshot graph is not the trend.
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
from utils import clamp


class TrendFollowingStrategy(StrategyPlugin):
    def name(self) -> str:
        return "trend_following"

    def describe(self) -> str:
        return "Trend from the 50- and 200-session averages and trend persistence."

    def required_fields(self) -> List[str]:
        return []

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        feats = trailing_features(context, symbol)
        above50 = None if not feats else feats.get("pct_above_50dma")
        if above50 is None:
            return unavailable_result(
                self.name(),
                "Trailing 50-session average unavailable; the 1-month graph is not used as the trend.",
            )

        above200 = feats.get("pct_above_200dma")
        persist = feats.get("trend_persistence")
        base = map_linear(float(above50), -10.0, 10.0)
        if persist is None:
            score = base
            confidence = 0.45
        else:
            score = clamp(base * (0.7 + 0.3 * float(persist)), 0.0, 100.0)
            confidence = 0.7
        if above200 is not None and (float(above200) > 0) != (float(above50) > 0) and abs(float(above50)) > 1.0:
            score = (score + 50.0) / 2.0
            confidence = min(confidence, 0.5)

        signal = POSITIVE if score >= 60 else NEGATIVE if score <= 40 else NEUTRAL
        above200_txt = "n/a" if above200 is None else f"{float(above200):+.2f}%"
        persist_txt = "n/a" if persist is None else f"{float(persist):.0%}"
        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=round(confidence, 2),
            signal=signal,
            reason=(f"Price {float(above50):+.2f}% vs 50-session average, "
                    f"{above200_txt} vs 200-session, persistence {persist_txt}."),
            data_used={
                "pct_above_50dma": above50,
                "pct_above_200dma": above200,
                "trend_persistence": persist,
            },
        )
