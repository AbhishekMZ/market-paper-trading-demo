"""VolatilityRiskStrategy — the same 20-session vol percentile the overlay uses.

A HIGH score means LOW volatility risk. The percentile is the one
`context.features.vol_percentile` computes (0 = calmest trailing window,
100 = most volatile). An extreme one-day move is still a risk flag; it is not
a second volatility definition.
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
from utils import clamp


class VolatilityRiskStrategy(StrategyPlugin):
    def name(self) -> str:
        return "volatility_risk"

    def describe(self) -> str:
        return "Stability from the trailing 20-session volatility percentile."

    def required_fields(self) -> List[str]:
        return []

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        feats = trailing_features(context, symbol)
        vp = None if not feats else feats.get("vol_percentile")
        if vp is None:
            return unavailable_result(
                self.name(),
                "Trailing volatility percentile unavailable; a 1-month dispersion is not used.",
            )

        warnings: List[str] = []
        risk_flags: List[str] = []
        # Percentile 0 (calm) -> 100. Percentile 100 (extreme) -> 0.
        base = 100.0 - float(vp)
        change_pct = market_data.get("change_pct") if isinstance(market_data, dict) else None
        if change_pct is not None and abs(float(change_pct)) >= 5.0:
            base -= 25.0
            risk_flags.append("extreme_daily_move")
        elif change_pct is not None and abs(float(change_pct)) >= 3.0:
            base -= 10.0
            risk_flags.append("large_daily_move")

        score = clamp(base, 0.0, 100.0)
        signal = POSITIVE if score >= 60 else NEGATIVE if score <= 40 else NEUTRAL
        move_txt = "n/a" if change_pct is None else f"{float(change_pct):+.2f}"
        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=0.7,
            signal=signal,
            reason=(f"20-session vol percentile {float(vp):.0f} "
                    f"(daily move {move_txt}%) -> stability {score:.0f}."),
            data_used={"vol_percentile": vp, "change_pct": change_pct},
            warnings=warnings,
            risk_flags=risk_flags,
        )
