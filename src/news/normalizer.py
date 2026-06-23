"""Normalize heterogeneous provider payloads into a clean NewsItem.

Handles the timestamp zoo: yfinance epoch seconds / ISO `pubDate`, GDELT's
`YYYYMMDDTHHMMSSZ` `seendate`. Anything unparseable yields a None timestamp
(treated as fresh-but-undated rather than dropped).
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any, Optional

from news.base import NewsItem


def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_published(value: Any) -> Optional[dt.datetime]:
    """Best-effort parse of a published timestamp into an aware UTC datetime."""
    if value is None or value == "":
        return None
    # Epoch seconds (yfinance providerPublishTime).
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.fromtimestamp(float(value), tz=dt.timezone.utc)
        except Exception:
            return None
    s = str(value).strip()
    # GDELT seendate: 20260623T101500Z
    m = re.fullmatch(r"(\d{8})T(\d{6})Z", s)
    if m:
        try:
            return dt.datetime.strptime(s, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
        except Exception:
            return None
    # ISO8601 (allow trailing Z).
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except Exception:
        return None


def _clean(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def to_news_item(
    *,
    symbol: str,
    provider: str,
    title: Optional[str],
    source: Optional[str] = None,
    url: Optional[str] = None,
    summary: Optional[str] = None,
    published: Any = None,
    fresh_hours: float = 24.0,
    max_age_hours: float = 96.0,
    raw: Optional[dict] = None,
) -> Optional[NewsItem]:
    """Build a NewsItem; returns None when there is no usable title."""
    clean_title = _clean(title)
    if not clean_title:
        return None
    pub = parse_published(published)
    age_hours: Optional[float] = None
    published_iso: Optional[str] = None
    is_fresh = True
    if pub is not None:
        published_iso = pub.isoformat()
        age_hours = round((_now_utc() - pub).total_seconds() / 3600.0, 2)
        is_fresh = age_hours <= fresh_hours
    return NewsItem(
        symbol=symbol,
        title=clean_title,
        source=_clean(source) or provider,
        provider=provider,
        url=url,
        summary=_clean(summary),
        published_at=published_iso,
        fetched_at=_now_utc().isoformat(),
        age_hours=age_hours,
        is_fresh=is_fresh,
        raw=raw or {},
    )
