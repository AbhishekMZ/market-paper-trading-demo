"""News-layer contracts: typed models + the NewsProvider interface.

The news layer is a RISK overlay. It runs AFTER the strategy/scoring layer and
can only ever make the system MORE cautious:

  * High/critical adverse news can BLOCK or downgrade a paper buy.
  * Positive news contributes at most a small, informational boost — it can
    NEVER, on its own, turn a non-buy into a buy. (See news.yml -> scoring.)

Everything downstream depends only on these models, so providers (yfinance,
GDELT, NewsAPI, …) stay swappable behind `NewsProvider`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NewsSentiment(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class NewsRiskLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NewsEventType(str, Enum):
    FRAUD = "FRAUD"
    REGULATORY = "REGULATORY"
    LEGAL = "LEGAL"
    RATING_DOWNGRADE = "RATING_DOWNGRADE"
    MANAGEMENT_CHANGE = "MANAGEMENT_CHANGE"
    EARNINGS_MISS = "EARNINGS_MISS"
    EARNINGS_BEAT = "EARNINGS_BEAT"
    ORDER_WIN = "ORDER_WIN"
    EXPANSION = "EXPANSION"
    MACRO = "MACRO"
    OTHER = "OTHER"


# Ordering so we can take "the worst risk across items" deterministically.
_RISK_RANK = {
    NewsRiskLevel.NONE: 0,
    NewsRiskLevel.LOW: 1,
    NewsRiskLevel.MEDIUM: 2,
    NewsRiskLevel.HIGH: 3,
    NewsRiskLevel.CRITICAL: 4,
}


def risk_rank(level: NewsRiskLevel) -> int:
    return _RISK_RANK.get(level, 0)


def max_risk(a: NewsRiskLevel, b: NewsRiskLevel) -> NewsRiskLevel:
    return a if risk_rank(a) >= risk_rank(b) else b


def coerce_risk(value: Any) -> NewsRiskLevel:
    try:
        return NewsRiskLevel(str(value).upper())
    except Exception:
        return NewsRiskLevel.NONE


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


@dataclass
class NewsItem:
    """One normalized news article relevant to a symbol."""

    symbol: str
    title: str
    source: str                       # publisher / outlet
    provider: str                     # which NewsProvider produced it (yfinance/gdelt/…)
    url: Optional[str] = None
    summary: str = ""
    published_at: Optional[str] = None  # ISO8601 (UTC) if known
    fetched_at: Optional[str] = None
    age_hours: Optional[float] = None
    is_fresh: bool = True
    sentiment: NewsSentiment = NewsSentiment.NEUTRAL
    relevance: float = 0.0            # 0..1
    event_types: List[str] = field(default_factory=list)
    risk_level: NewsRiskLevel = NewsRiskLevel.NONE
    matched_keywords: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {k: _plain(v) for k, v in asdict(self).items()}
        d.pop("raw", None)  # keep public payloads small / leak-free
        return d


@dataclass
class NewsRiskAssessment:
    """Per-symbol verdict the engine hands back to the signal pipeline."""

    symbol: str
    company_name: Optional[str] = None
    news_available: bool = False
    item_count: int = 0
    fresh_item_count: int = 0
    overall_sentiment: NewsSentiment = NewsSentiment.NEUTRAL
    news_risk_level: NewsRiskLevel = NewsRiskLevel.NONE
    dominant_event_types: List[str] = field(default_factory=list)
    blocks_buy: bool = False
    requires_manual_review: bool = False
    exit_review_for_holding: bool = False
    sentiment_boost: float = 0.0     # informational only; never creates a buy
    reasons: List[str] = field(default_factory=list)
    providers_used: List[str] = field(default_factory=list)
    top_items: List[Dict[str, Any]] = field(default_factory=list)
    critical_items: List[Dict[str, Any]] = field(default_factory=list)
    assessed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: _plain(v) for k, v in asdict(self).items()}


class NewsProvider(ABC):
    """Common contract for every news source.

    Implementations must degrade gracefully: any network/parse failure returns
    an empty list, NEVER raises. Missing news must never crash a paper run.
    """

    name: str = "base"
    enabled: bool = False

    @abstractmethod
    def fetch(
        self,
        symbol: str,
        company_name: Optional[str] = None,
        prefetched: Optional[List[Dict[str, Any]]] = None,
    ) -> List[NewsItem]:
        raise NotImplementedError
