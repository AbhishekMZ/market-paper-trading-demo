"""YahooFinanceProvider — market data via the `yfinance` library.

⚠️ UNOFFICIAL DATA SOURCE. yfinance is not affiliated with, endorsed, or vetted
by Yahoo; it uses Yahoo's publicly available endpoints and is intended for
research / educational / paper-trading use. Do NOT assume guaranteed uptime or
schema stability, and do NOT use it as a system of record for real trading.

Imports of yfinance/pandas are LAZY (inside methods) so the rest of the app can
import this module even if the libraries are absent; a missing library simply
yields an unusable snapshot and the system declines to trade (safe).
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from market_data.base import MarketDataProvider, MarketQuote, MarketSnapshot, PriceBar
from utils import now_ist_iso

UNOFFICIAL_WARNING = (
    "Yahoo Finance via yfinance is UNOFFICIAL (not affiliated with Yahoo); "
    "for research/paper-trading only."
)


def _is_nan(value: Any) -> bool:
    try:
        return value != value  # NaN != NaN
    except Exception:
        return False


def _safe_float(value: Any) -> Optional[float]:
    if value is None or _is_nan(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    if value is None or _is_nan(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class YahooFinanceProvider(MarketDataProvider):
    provider_name = "yfinance"

    def __init__(self, sleep_seconds: float = 1.0, max_retries: int = 2) -> None:
        self.sleep_seconds = float(sleep_seconds)
        self.max_retries = int(max_retries)

    # ------------------------------------------------------------------ #
    def get_snapshot(self, symbol: str, period: str = "1mo", interval: str = "1d") -> MarketSnapshot:
        try:
            import yfinance as yf  # lazy import
        except Exception as exc:  # library missing
            return self._empty_snapshot(symbol, [f"yfinance_unavailable: {exc}"])

        errors: List[str] = []
        bars: List[PriceBar] = []
        news: List[Dict[str, Any]] = []
        quote: Optional[MarketQuote] = None

        ticker = None
        for attempt in range(self.max_retries + 1):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period, interval=interval, auto_adjust=False)
                bars = self._history_to_bars(hist)
                if bars:
                    break
            except Exception as exc:
                errors.append(f"history_error(attempt {attempt}): {exc}")
                ticker = None
            if attempt < self.max_retries:
                time.sleep(self.sleep_seconds)

        if ticker is not None:
            fast_info = {}
            info: Dict[str, Any] = {}
            try:
                fast_info = getattr(ticker, "fast_info", {}) or {}
            except Exception as exc:
                errors.append(f"fast_info_error: {exc}")
            try:
                info = ticker.info or {}  # best-effort; can be slow/brittle
            except Exception as exc:
                errors.append(f"info_error: {exc}")
            try:
                quote = self._build_quote(symbol, fast_info, info, bars)
            except Exception as exc:
                errors.append(f"quote_error: {exc}")
            try:
                news = self._normalize_news(getattr(ticker, "news", []) or [])
            except Exception as exc:
                errors.append(f"news_error: {exc}")

        has_price = quote is not None and quote.current_price is not None
        data_quality = {
            "provider": self.provider_name,
            "symbol": symbol,
            "has_quote": has_price,
            "history_bars": len(bars),
            "has_news": len(news) > 0,
            "errors": errors,
            "is_usable": has_price and len(bars) >= 5,
            "warning": UNOFFICIAL_WARNING,
        }
        return MarketSnapshot(symbol=symbol, quote=quote, history=bars, news=news, data_quality=data_quality)

    def get_many_snapshots(
        self, symbols: List[str], period: str = "1mo", interval: str = "1d"
    ) -> List[MarketSnapshot]:
        out: List[MarketSnapshot] = []
        for i, symbol in enumerate(symbols):
            out.append(self.get_snapshot(symbol, period=period, interval=interval))
            if i < len(symbols) - 1 and self.sleep_seconds:
                time.sleep(self.sleep_seconds)  # be polite to Yahoo
        return out

    # ------------------------------------------------------------------ #
    def _history_to_bars(self, hist: Any) -> List[PriceBar]:
        if hist is None or getattr(hist, "empty", True):
            return []
        bars: List[PriceBar] = []
        for idx, row in hist.iterrows():
            ts = idx.isoformat() if hasattr(idx, "isoformat") else str(idx)
            bars.append(
                PriceBar(
                    timestamp=ts,
                    open=_safe_float(row.get("Open")),
                    high=_safe_float(row.get("High")),
                    low=_safe_float(row.get("Low")),
                    close=_safe_float(row.get("Close")),
                    volume=_safe_int(row.get("Volume")),
                )
            )
        return bars

    def _build_quote(self, symbol: str, fast_info: Any, info: Dict[str, Any], bars: List[PriceBar]) -> MarketQuote:
        def fi_get(key: str, default: Any = None) -> Any:
            try:
                return fast_info.get(key, default)
            except Exception:
                try:
                    return getattr(fast_info, key)
                except Exception:
                    return default

        current_price = _safe_float(fi_get("last_price"))
        price_source = "fast_info.last_price" if current_price is not None else "fallback"
        previous_close = _safe_float(fi_get("previous_close"))
        # Fall back to the last NON-NULL daily closes (the most recent bar can be
        # an incomplete/NaN session, e.g. today's bar off-hours).
        closes = [b.close for b in bars if b.close is not None]
        if current_price is None and closes:
            current_price = closes[-1]
            price_source = "history.close"
        if previous_close is None and len(closes) >= 2:
            previous_close = closes[-2]

        day_change = None
        day_change_pct = None
        if current_price is not None and previous_close not in (None, 0):
            day_change = round(current_price - previous_close, 4)
            day_change_pct = round(day_change / previous_close * 100, 4)

        return MarketQuote(
            symbol=symbol,
            name=info.get("longName") or info.get("shortName"),
            currency=fi_get("currency") or info.get("currency") or "INR",
            exchange=info.get("exchange") or info.get("fullExchangeName"),
            current_price=current_price,
            previous_close=previous_close,
            day_change=day_change,
            day_change_pct=day_change_pct,
            timestamp=now_ist_iso(),
            provider=self.provider_name,
            price_source=price_source,
            raw={
                "info_subset": {
                    "longName": info.get("longName"),
                    "shortName": info.get("shortName"),
                    "exchange": info.get("exchange"),
                    "currency": info.get("currency"),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                }
            },
        )

    def _normalize_news(self, raw_news: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for item in raw_news[:10]:
            if not isinstance(item, dict):
                continue
            # yfinance has used both flat and {'content': {...}} shapes over time.
            content = item.get("content") if isinstance(item.get("content"), dict) else item
            title = content.get("title") or item.get("title")
            if not title:
                continue
            out.append(
                {
                    "title": title,
                    "publisher": (content.get("provider") or {}).get("displayName")
                    if isinstance(content.get("provider"), dict)
                    else item.get("publisher"),
                    "link": item.get("link") or (content.get("canonicalUrl") or {}).get("url")
                    if isinstance(content.get("canonicalUrl"), dict)
                    else item.get("link"),
                    "provider_publish_time": item.get("providerPublishTime") or content.get("pubDate"),
                    "type": item.get("type") or content.get("contentType"),
                }
            )
        return out
