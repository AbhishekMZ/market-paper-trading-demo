"""MeanReversionStrategy — controlled pullbacks only, never falling knives.

EXPERIMENTAL in v1: display-only by default (contributes_to_score=false in
config/scoring.yml). It must be explicitly enabled before it can affect buys.
"""
from __future__ import annotations

from typing import Any, Dict, List

from strategy.base import (
    NEGATIVE,
    NEUTRAL,
    POSITIVE,
    StrategyPlugin,
    StrategyResult,
    trailing_features,
    unavailable_result,
)


class MeanReversionStrategy(StrategyPlugin):
    default_contributes_to_score = False

    def name(self) -> str:
        return "mean_reversion"

    def describe(self) -> str:
        return "Rewards controlled pullbacks within a healthy trend; penalizes sharp falls / falling knives."

    def required_fields(self) -> List[str]:
        return ["graph", "change_pct"]

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        feats = trailing_features(context, symbol)
        above50 = None if not feats else feats.get("pct_above_50dma")
        if above50 is None:
            return unavailable_result(
                self.name(),
                "Trailing averages unavailable; a short pullback on the 1-month graph is not used.",
            )

        above200 = feats.get("pct_above_200dma")
        change_pct = market_data.get("change_pct") if isinstance(market_data, dict) else None
        above50_f = float(above50)

        if change_pct is not None and float(change_pct) <= -4.0:
            score, signal = 25.0, NEGATIVE
            reason = f"Sharp fall {float(change_pct):.2f}% — treated as risk, not a buyable dip."
        elif above200 is not None and float(above200) > 0 and -8.0 <= above50_f <= -1.0:
            score, signal = 68.0, POSITIVE
            reason = (
                f"Pullback to {above50_f:+.2f}% vs the 50-session average "
                f"while still {float(above200):+.2f}% above the 200-session average."
            )
        elif above200 is not None and float(above200) <= 0:
            score, signal = 40.0, NEGATIVE
            reason = f"Below the 200-session average ({float(above200):+.2f}%) — not a constructive dip."
        else:
            score, signal = 52.0, NEUTRAL
            reason = "No clear mean-reversion setup on the trailing averages."

        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=score,
            confidence=0.55,
            signal=signal,
            reason=reason,
            data_used={"pct_above_50dma": above50, "pct_above_200dma": above200, "change_pct": change_pct},
        )
