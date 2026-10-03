"""BreakoutStrategy — momentum breakouts with trend confirmation.

EXPERIMENTAL in v1: display-only by default. Requires trend confirmation,
returns neutral on insufficient data, and avoids chasing extreme one-day moves.
"""
from __future__ import annotations

from typing import Any, Dict, List

from strategy.base import (
    NEUTRAL,
    POSITIVE,
    StrategyPlugin,
    StrategyResult,
    trailing_features,
    unavailable_result,
)


class BreakoutStrategy(StrategyPlugin):
    default_contributes_to_score = False

    def name(self) -> str:
        return "breakout"

    def describe(self) -> str:
        return "Flags momentum breakouts near the top of the recent range, confirmed by trend."

    def required_fields(self) -> List[str]:
        return ["graph"]

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        feats = trailing_features(context, symbol)
        pos = None if not feats else feats.get("range_position_2y")
        if pos is None:
            return unavailable_result(
                self.name(),
                "Trailing range position unavailable; the 1-month graph is not used.",
            )

        change_pct = market_data.get("change_pct") if isinstance(market_data, dict) else None
        persist = float(feats.get("trend_persistence") or 0.0)
        above200 = feats.get("pct_above_200dma")
        trend_up = persist >= 0.55 and (above200 is None or float(above200) > 0)

        if change_pct is not None and float(change_pct) >= 5.0:
            score, signal = 45.0, NEUTRAL
            reason = f"Already up {float(change_pct):.2f}% today — avoid chasing an extended move."
        elif float(pos) >= 0.9 and trend_up:
            score, signal = 70.0, POSITIVE
            reason = f"Near the trailing range high ({float(pos):.0%}) with trend persistence {persist:.0%}."
        elif float(pos) >= 0.9:
            score, signal = 50.0, NEUTRAL
            reason = "Near the trailing range high but the longer trend is not confirmed."
        else:
            score, signal = 48.0, NEUTRAL
            reason = f"No breakout ({float(pos):.0%} of the trailing range)."

        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=score,
            confidence=0.55,
            signal=signal,
            reason=reason,
            data_used={"range_position_2y": pos, "trend_persistence": persist, "change_pct": change_pct},
        )
