"""RelativeStrengthStrategy — prefer stocks outperforming the benchmark."""
from __future__ import annotations

from typing import Any, Dict, List

from strategy.base import NEGATIVE, NEUTRAL, POSITIVE, StrategyPlugin, StrategyResult, map_linear


class RelativeStrengthStrategy(StrategyPlugin):
    def name(self) -> str:
        return "relative_strength"

    def describe(self) -> str:
        return "Compares a stock's recent move against the benchmark index; rewards outperformance."

    def required_fields(self) -> List[str]:
        return ["change_pct"]

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        stock = market_data.get("change_pct")
        bench = context.get("benchmark_change_pct")
        warnings: List[str] = []

        if stock is None:
            return StrategyResult(self.name(), 50.0, 0.1, NEUTRAL,
                                  "No stock change available for relative strength.",
                                  warnings=["missing_change_pct"], is_valid=False)

        if bench is None:
            # Fallback: absolute momentum, clearly flagged as lower-confidence.
            score = map_linear(stock, -3.0, 3.0)
            warnings.append("No benchmark data; using absolute momentum as a proxy.")
            confidence = 0.3
            rel = None
            reason = f"No benchmark; absolute move {stock:+.2f}% used as RS proxy."
        else:
            rel = stock - bench
            score = map_linear(rel, -2.0, 2.0)
            confidence = 0.6
            reason = f"Stock {stock:+.2f}% vs benchmark {bench:+.2f}% -> relative {rel:+.2f}%."

        signal = POSITIVE if score >= 60 else NEGATIVE if score <= 40 else NEUTRAL
        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=confidence,
            signal=signal,
            reason=reason,
            data_used={"stock_change_pct": stock, "benchmark_change_pct": bench, "relative_pct": rel},
            warnings=warnings,
        )
