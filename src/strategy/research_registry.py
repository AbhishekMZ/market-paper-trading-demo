"""ResearchRegistry — document strategy ideas as HYPOTHESES, not trusted rules.

Loads config/research_hypotheses.yml. Enforces the core principle: no online /
popular strategy is valid by default; its validation_status controls whether it
may ever inform real trading.
"""
from __future__ import annotations

from typing import Any, Dict, List

import storage

# Statuses that permit a strategy to be considered for (future) real trading.
REAL_TRADING_ELIGIBLE = {"accepted_for_manual_review", "accepted_for_limited_live_later"}
VALID_STATUSES = {
    "untested", "paper_testing", "rejected",
    "accepted_for_manual_review", "accepted_for_limited_live_later",
}


class ResearchRegistry:
    def __init__(self) -> None:
        cfg = storage.load_config("research_hypotheses.yml")
        self.hypotheses: List[Dict[str, Any]] = cfg.get("hypotheses", []) or []

    def all(self) -> List[Dict[str, Any]]:
        return self.hypotheses

    def by_strategy(self, strategy_name: str) -> List[Dict[str, Any]]:
        return [h for h in self.hypotheses if h.get("strategy_name") == strategy_name]

    def status_of(self, strategy_name: str) -> str:
        hyps = self.by_strategy(strategy_name)
        return hyps[0].get("validation_status", "untested") if hyps else "untested"

    def is_real_trading_eligible(self, strategy_name: str) -> bool:
        """A strategy may inform real trading only if a hypothesis is accepted."""
        return any(
            h.get("validation_status") in REAL_TRADING_ELIGIBLE
            for h in self.by_strategy(strategy_name)
        )

    def currently_testing(self) -> List[Dict[str, Any]]:
        return [h for h in self.hypotheses if h.get("validation_status") == "paper_testing"]

    def summary(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for h in self.hypotheses:
            s = h.get("validation_status", "untested")
            counts[s] = counts.get(s, 0) + 1
        return {
            "total": len(self.hypotheses),
            "by_status": counts,
            "testing": [h["hypothesis_id"] for h in self.currently_testing()],
            "real_trading_eligible": [
                h["strategy_name"] for h in self.hypotheses
                if h.get("validation_status") in REAL_TRADING_ELIGIBLE
            ],
        }
