"""Market-data provider abstraction + normalized models.

The rest of the system (regime engine, strategy plugins, hybrid engine) depends
ONLY on these normalized models — never on yfinance/yahooquery/SerpApi directly.
That keeps providers swappable: Yahoo (yfinance) now, yahooquery / NSE / Angel
One market data / a paid feed later, with no strategy changes.

`MarketSnapshot.to_market_data()` flattens a snapshot into the simple dict the
strategy layer consumes, so providers stay the single normalization boundary.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from utils import now_ist_iso


@dataclass
class PriceBar:
    timestamp: str
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]


@dataclass
class MarketQuote:
    symbol: str
    name: Optional[str]
    currency: Optional[str]
    exchange: Optional[str]
    current_price: Optional[float]
    previous_close: Optional[float]
    day_change: Optional[float]
    day_change_pct: Optional[float]
    timestamp: str
    provider: str
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketSnapshot:
    symbol: str
    quote: Optional[MarketQuote]
    history: List[PriceBar]
    news: List[Dict[str, Any]]
    data_quality: Dict[str, Any]

    @property
    def is_usable(self) -> bool:
        return bool(self.data_quality.get("is_usable"))

    def to_market_data(self, name: Optional[str] = None, exchange: Optional[str] = None) -> Dict[str, Any]:
        """Flatten into the normalized dict the strategy layer expects."""
        q = self.quote
        price = q.current_price if q else None
        graph = [
            {"price": b.close, "date": b.timestamp}
            for b in self.history
            if b.close is not None
        ]
        headlines = [n.get("title") for n in self.news if n.get("title")]
        return {
            "ok": price is not None,
            "symbol": self.symbol,
            "name": name or (q.name if q else None) or self.symbol,
            "exchange": exchange or (q.exchange if q else None) or "NSE",
            "price": price,
            "currency": (q.currency if q else None) or "INR",
            "previous_close": q.previous_close if q else None,
            "change": q.day_change if q else None,
            "change_pct": q.day_change_pct if q else None,
            "graph": graph,
            "graph_points": len(graph),
            "headlines": headlines,
            "news_available": len(headlines) > 0,
            "extracted_at": q.timestamp if q else now_ist_iso(),
            "source": q.provider if q else "unknown",
            "reason": "" if price is not None else "; ".join(self.data_quality.get("errors", []) or ["no price"]),
        }


class MarketDataProvider(ABC):
    """Common contract every market-data provider implements."""

    provider_name: str = "base"

    @abstractmethod
    def get_snapshot(self, symbol: str, period: str = "1mo", interval: str = "1d") -> MarketSnapshot:
        raise NotImplementedError

    @abstractmethod
    def get_many_snapshots(
        self, symbols: List[str], period: str = "1mo", interval: str = "1d"
    ) -> List[MarketSnapshot]:
        raise NotImplementedError

    # Shared helper for "no data" snapshots.
    def _empty_snapshot(self, symbol: str, errors: List[str]) -> MarketSnapshot:
        return MarketSnapshot(
            symbol=symbol,
            quote=None,
            history=[],
            news=[],
            data_quality={
                "provider": self.provider_name,
                "symbol": symbol,
                "has_quote": False,
                "history_bars": 0,
                "has_news": False,
                "errors": errors,
                "is_usable": False,
            },
        )
