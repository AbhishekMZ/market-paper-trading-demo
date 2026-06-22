"""Strategy plugin contract.

Every strategy is a plugin implementing StrategyPlugin and returning a
StrategyResult. Strategies produce EVIDENCE and a 0-100 score contribution
only — they NEVER place trades. The HybridSignalEngine combines them.

Determinism rule (v1): given the same market_data + portfolio_state +
context, a plugin must always return the same result. No ML, no randomness,
no hidden state, no self-tuning.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from utils import clamp, now_ist_iso


# Signal direction a strategy contributes (qualitative, for explainability).
POSITIVE = "POSITIVE"
NEUTRAL = "NEUTRAL"
NEGATIVE = "NEGATIVE"


@dataclass
class StrategyResult:
    strategy_name: str
    score_contribution: float          # 0-100 sub-score
    confidence: float                  # 0-1
    signal: str                        # POSITIVE | NEUTRAL | NEGATIVE
    reason: str
    data_used: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=now_ist_iso)
    error: Optional[str] = None
    is_valid: bool = True
    contributes_to_score: bool = True
    display_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def neutral_result(name: str, reason: str, warnings: Optional[List[str]] = None,
                   contributes: bool = True, display_only: bool = False) -> StrategyResult:
    """A safe, score-neutral result (50/100, low confidence)."""
    return StrategyResult(
        strategy_name=name,
        score_contribution=50.0,
        confidence=0.2,
        signal=NEUTRAL,
        reason=reason,
        warnings=warnings or [],
        contributes_to_score=contributes,
        display_only=display_only,
    )


def map_linear(value: Optional[float], lo: float, hi: float, default: float = 50.0) -> float:
    """Map value in [lo, hi] to [0, 100], clamped. Returns default if None."""
    if value is None:
        return default
    if hi == lo:
        return default
    return clamp((value - lo) / (hi - lo) * 100.0, 0.0, 100.0)


class StrategyPlugin(ABC):
    """Base class all strategy plugins implement."""

    #: Whether this strategy contributes to the final score (vs display-only).
    default_contributes_to_score: bool = True

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def describe(self) -> str:
        ...

    @abstractmethod
    def required_fields(self) -> List[str]:
        """Normalized market_data fields this strategy needs."""
        ...

    @abstractmethod
    def evaluate(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        context: Dict[str, Any],
    ) -> StrategyResult:
        ...

    def explain(self, result: StrategyResult) -> str:
        return f"[{result.strategy_name}] {result.signal} {result.score_contribution:.0f}/100 — {result.reason}"

    # Shared helpers ----------------------------------------------------- #
    def _missing_fields(self, market_data: Dict[str, Any]) -> List[str]:
        return [f for f in self.required_fields() if market_data.get(f) in (None, [], "")]

    @staticmethod
    def _prices(market_data: Dict[str, Any]) -> List[float]:
        return [p["price"] for p in (market_data.get("graph") or []) if p.get("price") is not None]

    def _safe_evaluate(self, *args: Any, **kwargs: Any) -> StrategyResult:
        """Wrapper that converts unexpected errors into an invalid, neutral result."""
        try:
            return self.evaluate(*args, **kwargs)
        except Exception as exc:  # never let one plugin crash the run
            return StrategyResult(
                strategy_name=self.name(),
                score_contribution=50.0,
                confidence=0.0,
                signal=NEUTRAL,
                reason=f"Strategy errored and was ignored: {exc}",
                error=str(exc),
                is_valid=False,
            )
