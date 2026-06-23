"""Typed order / signal / decision models.

These form the broker-agnostic contract between the strategy layer
(signal/risk/execution engines) and the broker adapters.

SAFETY: v1 is paper-trading only. OrderRequest enforces delivery-only,
limit-only constraints at construction time, so an invalid order can
never be handed to a broker adapter.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from utils import gen_id, now_ist_iso


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    # The following exist only so we can explicitly reject them.
    MARKET = "MARKET"
    SL = "SL"
    SL_M = "SL-M"


class ProductType(str, Enum):
    DELIVERY = "DELIVERY"
    # Explicitly rejected product types.
    INTRADAY = "INTRADAY"
    MARGIN = "MARGIN"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"


class Validity(str, Enum):
    DAY = "DAY"


class OrderState(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"


class SignalLabel(str, Enum):
    BUY_SMALL_PAPER = "BUY_SMALL_PAPER"
    WATCH = "WATCH"
    HOLD = "HOLD"
    NO_ACTION = "NO_ACTION"
    DO_NOT_BUY = "DO_NOT_BUY"
    SELL_REVIEW = "SELL_REVIEW"
    TRIM_REVIEW = "TRIM_REVIEW"
    EXIT_REVIEW = "EXIT_REVIEW"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    HIGH_RISK_IGNORE = "HIGH_RISK_IGNORE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DataQuality(str, Enum):
    GOOD = "GOOD"
    ACCEPTABLE = "ACCEPTABLE"
    WEAK = "WEAK"
    MISSING = "MISSING"


# Hard allow-lists for v1. Anything outside these is rejected.
ALLOWED_ORDER_TYPES = {OrderType.LIMIT}
ALLOWED_PRODUCT_TYPES = {ProductType.DELIVERY}


class OrderValidationError(ValueError):
    """Raised when an OrderRequest violates the v1 safety constraints."""


def _coerce(enum_cls, value):
    if isinstance(value, enum_cls):
        return value
    return enum_cls(str(value).upper() if enum_cls is not Validity else str(value).upper())


def _to_plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return value


# --------------------------------------------------------------------------- #
# OrderRequest
# --------------------------------------------------------------------------- #
@dataclass
class OrderRequest:
    symbol: str
    side: OrderSide
    quantity: int
    amount: float
    order_type: OrderType = OrderType.LIMIT
    product_type: ProductType = ProductType.DELIVERY
    validity: Validity = Validity.DAY
    limit_price: Optional[float] = None
    exchange: str = "NSE"
    reason: str = ""
    is_paper: bool = True
    requires_approval: bool = False
    generated_by_signal_id: Optional[str] = None
    order_id: str = field(default_factory=lambda: gen_id("ord"))
    created_at: str = field(default_factory=now_ist_iso)

    def __post_init__(self) -> None:
        # Coerce string inputs to enums so callers can pass either.
        self.side = _coerce(OrderSide, self.side)
        self.order_type = _coerce(OrderType, self.order_type)
        self.product_type = _coerce(ProductType, self.product_type)
        self.validity = _coerce(Validity, self.validity)
        self.validate()

    def validate(self) -> None:
        if self.order_type not in ALLOWED_ORDER_TYPES:
            raise OrderValidationError(
                f"order_type must be LIMIT in this project (got {self.order_type.value}). "
                "Market / SL orders are blocked."
            )
        if self.product_type not in ALLOWED_PRODUCT_TYPES:
            raise OrderValidationError(
                f"product_type must be DELIVERY (got {self.product_type.value}). "
                "Intraday / margin / F&O are blocked."
            )
        if self.side not in (OrderSide.BUY, OrderSide.SELL):
            raise OrderValidationError(f"side must be BUY or SELL (got {self.side}).")
        if self.quantity is None or self.quantity <= 0:
            raise OrderValidationError("quantity must be a positive integer.")
        if self.amount is None or self.amount <= 0:
            raise OrderValidationError("amount must be positive.")
        if self.order_type == OrderType.LIMIT and (self.limit_price is None or self.limit_price <= 0):
            raise OrderValidationError("LIMIT order requires a positive limit_price.")

    def to_dict(self) -> Dict[str, Any]:
        return {k: _to_plain(v) for k, v in asdict(self).items()}


# --------------------------------------------------------------------------- #
# OrderResult / OrderStatus
# --------------------------------------------------------------------------- #
@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: OrderSide
    status: OrderState
    quantity: int
    filled_quantity: int
    price: Optional[float]
    amount: float
    is_paper: bool
    broker_adapter: str
    message: str = ""
    reason: str = ""
    signal_id: Optional[str] = None
    timestamp: str = field(default_factory=now_ist_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {k: _to_plain(v) for k, v in asdict(self).items()}

    @property
    def accepted(self) -> bool:
        return self.status in (OrderState.FILLED, OrderState.ACCEPTED, OrderState.PARTIALLY_FILLED)


@dataclass
class OrderStatus:
    order_id: str
    status: OrderState
    filled_quantity: int = 0
    average_price: Optional[float] = None
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {k: _to_plain(v) for k, v in asdict(self).items()}


# --------------------------------------------------------------------------- #
# TradeSignal
# --------------------------------------------------------------------------- #
@dataclass
class TradeSignal:
    signal_id: str
    symbol: str
    name: str
    exchange: str
    score: float
    label: SignalLabel
    risk_level: RiskLevel
    confidence: float
    data_quality: DataQuality
    reason: str
    last_price: Optional[float] = None
    checkpoint: str = ""
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    # Hybrid-strategy fields.
    market_regime: str = ""
    strategy_results: List[Dict[str, Any]] = field(default_factory=list)
    conflict_warnings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    led_to_paper_trade: bool = False
    data_snapshot: Dict[str, Any] = field(default_factory=dict)
    # Data-quality provenance (DataQualityEngine).
    price_source: str = "unknown"
    entry_price_used: Optional[float] = None
    mtm_price_used: Optional[float] = None
    price_consistency_check: str = "PASSED"
    data_quality_verdict: str = "OK"
    # News-risk overlay (NewsRiskEngine). News can only ADD caution.
    news_available: bool = False
    news_risk_level: str = "NONE"
    news_sentiment: str = "NEUTRAL"
    news_event_types: List[str] = field(default_factory=list)
    news_blocks_buy: bool = False
    news_item_count: int = 0
    news_top_headline: Optional[str] = None
    news_reasons: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_ist_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {k: _to_plain(v) for k, v in asdict(self).items()}


# --------------------------------------------------------------------------- #
# RiskDecision
# --------------------------------------------------------------------------- #
@dataclass
class RiskDecision:
    approved: bool
    symbol: str
    reason: str
    rules_checked: List[str] = field(default_factory=list)
    rules_failed: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    created_at: str = field(default_factory=now_ist_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {k: _to_plain(v) for k, v in asdict(self).items()}


# --------------------------------------------------------------------------- #
# ApprovalDecision (used by manual-approval mode in later phases)
# --------------------------------------------------------------------------- #
@dataclass
class ApprovalDecision:
    approval_id: str
    order_id: str
    symbol: str
    status: str  # PENDING | APPROVED | REJECTED
    requested_at: str = field(default_factory=now_ist_iso)
    decided_at: Optional[str] = None
    decided_by: Optional[str] = None
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {k: _to_plain(v) for k, v in asdict(self).items()}
