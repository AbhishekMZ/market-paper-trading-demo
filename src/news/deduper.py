"""De-duplicate news items across providers.

The same story often appears via yfinance AND GDELT (and multiple outlets). We
collapse near-identical titles so one event isn't counted as many. yfinance is
preferred as the canonical copy (already symbol-tagged), then the freshest item.
"""
from __future__ import annotations

import re
from typing import List

from news.base import NewsItem

_WORD = re.compile(r"[a-z0-9]+")


def _fingerprint(title: str) -> str:
    # Order-insensitive bag of the first significant words.
    words = _WORD.findall((title or "").lower())
    words = [w for w in words if len(w) > 2][:8]
    return " ".join(sorted(words))


def _rank(item: NewsItem) -> tuple:
    provider_pref = 0 if item.provider == "yfinance" else 1
    # Newer first (smaller age preferred); undated treated as moderately fresh.
    age = item.age_hours if item.age_hours is not None else 48.0
    return (provider_pref, age)


def dedupe(items: List[NewsItem]) -> List[NewsItem]:
    best: dict = {}
    for it in items:
        fp = _fingerprint(it.title)
        if not fp:
            fp = (it.url or it.title or "").lower()
        cur = best.get(fp)
        if cur is None or _rank(it) < _rank(cur):
            best[fp] = it
    # Stable-ish ordering: freshest first.
    return sorted(best.values(), key=lambda i: (i.age_hours if i.age_hours is not None else 48.0))
