"""Observation-layer contracts: trigger + escalation models.

The Observation & Escalation Engine watches a small active watchlist between the
heavy deep-analysis checkpoints, detects meaningful changes, and escalates them.
It NEVER places real orders and NEVER bypasses the risk / news / data-quality /
execution gates — any paper action it takes goes through the same ExecutionEngine
as the deep pipeline.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from utils import gen_id, now_ist_iso


class TriggerType(str, Enum):
    PRICE_BREAKOUT = "PRICE_BREAKOUT"
    PRICE_BREAKDOWN = "PRICE_BREAKDOWN"
    LARGE_MOVE = "LARGE_MOVE"
    GAP_MOVE = "GAP_MOVE"
    SOFT_LOSS_REVIEW = "SOFT_LOSS_REVIEW"
    STRONG_LOSS_REVIEW = "STRONG_LOSS_REVIEW"
    HARD_LOSS_REVIEW = "HARD_LOSS_REVIEW"
    PROFIT_REVIEW = "PROFIT_REVIEW"
    HIGH_RISK_NEWS = "HIGH_RISK_NEWS"
    CRITICAL_NEWS = "CRITICAL_NEWS"
    MARKET_REGIME_SHIFT = "MARKET_REGIME_SHIFT"
    DATA_ANOMALY = "DATA_ANOMALY"
    STALE_QUOTE = "STALE_QUOTE"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    BUY_CANDIDATE_RECHECK = "BUY_CANDIDATE_RECHECK"
    NEWS_BLOCK_RECHECK = "NEWS_BLOCK_RECHECK"


class TriggerSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TriggerStatus(str, Enum):
    DETECTED = "DETECTED"
    THROTTLED = "THROTTLED"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"


class ActionType(str, Enum):
    OBSERVE_ONLY = "OBSERVE_ONLY"
    FOCUSED_REANALYSIS = "FOCUSED_REANALYSIS"
    PAPER_BUY_REVIEW = "PAPER_BUY_REVIEW"
    PAPER_BUY_ALLOWED = "PAPER_BUY_ALLOWED"
    SELL_REVIEW = "SELL_REVIEW"
    TRIM_REVIEW = "TRIM_REVIEW"
    EXIT_REVIEW = "EXIT_REVIEW"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    BLOCKED_BY_RISK = "BLOCKED_BY_RISK"
    BLOCKED_BY_NEWS = "BLOCKED_BY_NEWS"
    BLOCKED_BY_DATA_QUALITY = "BLOCKED_BY_DATA_QUALITY"


_SEV_RANK = {TriggerSeverity.INFO: 0, TriggerSeverity.LOW: 1, TriggerSeverity.MEDIUM: 2,
             TriggerSeverity.HIGH: 3, TriggerSeverity.CRITICAL: 4}


def severity_rank(s: TriggerSeverity) -> int:
    return _SEV_RANK.get(s, 0)


def _plain(v: Any) -> Any:
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, list):
        return [_plain(x) for x in v]
    return v


@dataclass
class TriggerEvent:
    symbol: str
    trigger_type: TriggerType
    severity: TriggerSeverity
    reason: str
    company_name: Optional[str] = None
    status: TriggerStatus = TriggerStatus.DETECTED
    source: str = "observation"
    price_at_detection: Optional[float] = None
    previous_price: Optional[float] = None
    change_pct: Optional[float] = None
    market_regime: Optional[str] = None
    news_event_ids: List[str] = field(default_factory=list)
    data_quality_flags: List[str] = field(default_factory=list)
    recommended_next_step: str = ""
    requires_focused_analysis: bool = False
    blocks_action: bool = False
    created_escalation_id: Optional[str] = None
    trigger_id: str = field(default_factory=lambda: gen_id("trg"))
    detected_at: str = field(default_factory=now_ist_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {k: _plain(v) for k, v in asdict(self).items()}

    def cooldown_key(self) -> str:
        return f"{self.symbol}:{self.trigger_type.value}"


@dataclass
class EscalationItem:
    symbol: str
    severity: TriggerSeverity
    action_type: ActionType
    reason: str
    trigger_ids: List[str] = field(default_factory=list)
    action_status: str = "OPEN"        # OPEN | DONE | EXPIRED
    focused_analysis_required: bool = False
    focused_analysis_result: Optional[Dict[str, Any]] = None
    manual_review_required: bool = False
    email_sent: bool = False
    final_decision: str = ""
    escalation_id: str = field(default_factory=lambda: gen_id("esc"))
    created_at: str = field(default_factory=now_ist_iso)
    expires_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: _plain(v) for k, v in asdict(self).items()}


@dataclass
class ObservationResult:
    checkpoint: str
    mode: str
    observed_symbols: List[str] = field(default_factory=list)
    open_positions_observed: List[str] = field(default_factory=list)
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    throttled: List[Dict[str, Any]] = field(default_factory=list)
    escalations: List[Dict[str, Any]] = field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    blocked_actions: List[Dict[str, Any]] = field(default_factory=list)
    emails_sent: int = 0
    as_of: str = field(default_factory=now_ist_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {k: _plain(v) for k, v in asdict(self).items()}
