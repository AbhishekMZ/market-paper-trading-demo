"""Walk-forward validation SKELETON (intentionally not implemented in v1).

Walk-forward validation is the right tool to avoid overfitting before any real
trading: optimize on an in-sample window, validate on the next out-of-sample
window, roll forward, and require out-of-sample robustness.

We ship the SHAPE here so the project is structured for it, but we do not fake
results. Implement only when there is a clean, point-in-time price history and
after reading docs/strategy_validation_principles.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class WalkForwardWindow:
    in_sample_start: str
    in_sample_end: str
    out_of_sample_start: str
    out_of_sample_end: str


class WalkForwardValidator:
    def __init__(self, in_sample_days: int = 60, out_of_sample_days: int = 20, step_days: int = 20) -> None:
        self.in_sample_days = in_sample_days
        self.out_of_sample_days = out_of_sample_days
        self.step_days = step_days

    def plan_windows(self, start_date: str, end_date: str) -> List[WalkForwardWindow]:
        """PLACEHOLDER: would generate rolling in/out-of-sample windows."""
        raise NotImplementedError(
            "Walk-forward windowing is a documented placeholder in v1. "
            "Requires point-in-time historical data not available on the free tier."
        )

    def validate(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError(
            "Walk-forward validation is intentionally unimplemented in v1 to avoid "
            "presenting unvalidated or overfit results. See docs/strategy_validation_principles.md."
        )
