"""VolatilityRiskStrategy — penalize noisy / unstable stocks.

A HIGH score means LOW volatility risk (calmer = safer = more buyable). Extreme
one-day moves, large dispersion, and data gaps all reduce the score.
"""
from __future__ import annotations

import statistics
from typing import Any, Dict, List

from strategy.base import NEGATIVE, NEUTRAL, POSITIVE, StrategyPlugin, StrategyResult, map_linear
from utils import clamp


class VolatilityRiskStrategy(StrategyPlugin):
    def name(self) -> str:
        return "volatility_risk"

    def describe(self) -> str:
        return "Scores stability: penalizes extreme daily moves, high dispersion, and data gaps."

    def required_fields(self) -> List[str]:
        return ["graph"]

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        prices = self._prices(market_data)
        change_pct = market_data.get("change_pct")
        warnings: List[str] = []
        risk_flags: List[str] = []

        # Volatility is measured on RETURNS (detrended), not on price levels —
        # otherwise a clean up-trend would be mislabelled as "volatile".
        vol_pct = None
        if len(prices) >= 4:
            returns = [(b - a) / a for a, b in zip(prices, prices[1:]) if a]
            if len(returns) >= 2:
                vol_pct = statistics.pstdev(returns) * 100.0
        else:
            warnings.append("Sparse price series (data gap); volatility under-measured.")
            risk_flags.append("data_gap")

        # Base stability score from dispersion (low vol -> high score).
        if vol_pct is None:
            base = 55.0
            confidence = 0.25
        else:
            # ~0% return-stdev -> calm (high score); ~2.5% -> noisy (low score).
            base = 100.0 - map_linear(vol_pct, 0.0, 2.5)
            confidence = 0.6

        # Penalize an extreme one-day move.
        if change_pct is not None and abs(change_pct) >= 5.0:
            base -= 25.0
            risk_flags.append("extreme_daily_move")
        elif change_pct is not None and abs(change_pct) >= 3.0:
            base -= 10.0
            risk_flags.append("large_daily_move")

        score = clamp(base, 0.0, 100.0)
        signal = POSITIVE if score >= 60 else NEGATIVE if score <= 40 else NEUTRAL
        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=confidence,
            signal=signal,
            reason=(
                f"Volatility {vol_pct:.2f}% / daily move {change_pct if change_pct is not None else 'n/a'}% "
                f"-> stability score {score:.0f}." if vol_pct is not None
                else f"Volatility unknown (data gap); stability score {score:.0f}."
            ),
            data_used={"volatility_pct": round(vol_pct, 3) if vol_pct is not None else None,
                       "change_pct": change_pct},
            warnings=warnings,
            risk_flags=risk_flags,
        )
