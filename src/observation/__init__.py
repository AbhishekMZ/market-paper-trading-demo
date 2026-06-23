"""Observation & Escalation Engine — lightweight between-checkpoint monitoring.

Public surface:
    ObservationEngine — run(checkpoint) -> ObservationResult (observe watchlist +
                        positions, detect triggers, escalate)
    WatchlistManager  — build the small active watchlist
    FocusedAnalysis   — re-run the full decision stack for one symbol

Safety invariants (enforced, not just documented): observation never places real
orders, never bypasses Risk/News/DataQuality/ExecutionEngine, never auto-sells.
Any swift paper action flows through ExecutionEngine.process_buy.
"""
from __future__ import annotations

from observation.escalation_engine import EscalationEngine
from observation.focused_analysis import FocusedAnalysis
from observation.observation_engine import ObservationEngine
from observation.trigger_models import (
    ActionType,
    EscalationItem,
    ObservationResult,
    TriggerEvent,
    TriggerSeverity,
    TriggerStatus,
    TriggerType,
)
from observation.watchlist_manager import WatchlistManager

__all__ = [
    "ObservationEngine",
    "WatchlistManager",
    "FocusedAnalysis",
    "EscalationEngine",
    "TriggerEvent",
    "EscalationItem",
    "ObservationResult",
    "TriggerType",
    "TriggerSeverity",
    "TriggerStatus",
    "ActionType",
]
