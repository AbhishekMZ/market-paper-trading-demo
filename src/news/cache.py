"""File-backed news cache (TTL) — keeps the free GDELT API polite & ₹0-cost.

Only the network provider (GDELT) needs caching; yfinance news rides along with
the price snapshot already in memory. Cache stores raw article dicts keyed by
"provider:symbol"; a miss or stale entry simply triggers a fresh fetch.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

import storage
from utils import read_json, write_json

_CACHE_FILE = "news_cache.json"


def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class NewsCache:
    def __init__(self, cfg: Dict[str, Any]) -> None:
        cache_cfg = (cfg or {}).get("cache", {})
        self.enabled = bool(cache_cfg.get("enabled", True))
        self.ttl_minutes = float(cache_cfg.get("ttl_minutes", 60))
        self.path = storage.state_file(_CACHE_FILE)
        self.store: Dict[str, Any] = read_json(self.path, {}) if self.enabled else {}
        if not isinstance(self.store, dict):
            self.store = {}

    def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        if not self.enabled:
            return None
        entry = self.store.get(key)
        if not isinstance(entry, dict):
            return None
        fetched = entry.get("fetched_at")
        try:
            ts = dt.datetime.fromisoformat(str(fetched))
        except Exception:
            return None
        age_min = (_now_utc() - ts).total_seconds() / 60.0
        if age_min > self.ttl_minutes:
            return None
        items = entry.get("items")
        return items if isinstance(items, list) else None

    def put(self, key: str, items: List[Dict[str, Any]]) -> None:
        if not self.enabled:
            return
        self.store[key] = {"fetched_at": _now_utc().isoformat(), "items": items}

    def save(self) -> None:
        if not self.enabled:
            return
        # Bound the cache so it can't grow without limit in the repo.
        if len(self.store) > 200:
            keys = sorted(self.store, key=lambda k: self.store[k].get("fetched_at", ""))[-200:]
            self.store = {k: self.store[k] for k in keys}
        write_json(self.path, self.store)
