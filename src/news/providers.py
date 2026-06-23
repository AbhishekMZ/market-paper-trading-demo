"""News providers — swappable sources behind the NewsProvider contract.

* YFinanceNewsProvider — reuses headlines already fetched with the price
  snapshot (zero extra cost); falls back to a direct yfinance pull if needed.
* GDELTNewsProvider — GDELT 2.0 Doc API. Free, no key. Network call wrapped in
  a short timeout + cache; ANY failure degrades to "no news" (never raises).
* NewsAPIProvider — key-gated, intentionally DISABLED in v1.

Providers return raw NewsItems (title/source/url/time); the engine enriches them
with sentiment / relevance / event classification.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from news.base import NewsItem, NewsProvider
from news.cache import NewsCache
from news.normalizer import to_news_item


class YFinanceNewsProvider(NewsProvider):
    name = "yfinance"

    def __init__(self, cfg: Dict[str, Any], news_cfg: Dict[str, Any]) -> None:
        self.enabled = bool(cfg.get("enabled", True))
        self.max_items = int(cfg.get("max_items", 10))
        fresh = (news_cfg or {}).get("freshness", {})
        self.fresh_hours = float(fresh.get("fresh_hours", 24))
        self.max_age_hours = float(fresh.get("max_age_hours", 96))

    def fetch(self, symbol, company_name=None, prefetched=None) -> List[NewsItem]:
        if not self.enabled:
            return []
        raw_items = prefetched
        if raw_items is None:
            raw_items = self._direct_pull(symbol)
        out: List[NewsItem] = []
        for art in (raw_items or [])[: self.max_items]:
            if not isinstance(art, dict):
                continue
            item = to_news_item(
                symbol=symbol,
                provider=self.name,
                title=art.get("title"),
                source=art.get("publisher") or art.get("source"),
                url=art.get("link") or art.get("url"),
                summary=art.get("summary"),
                published=art.get("provider_publish_time") or art.get("published"),
                fresh_hours=self.fresh_hours,
                max_age_hours=self.max_age_hours,
            )
            if item:
                out.append(item)
        return out

    def _direct_pull(self, symbol: str) -> List[Dict[str, Any]]:
        try:
            import yfinance as yf  # lazy
            raw = getattr(yf.Ticker(symbol), "news", []) or []
        except Exception:
            return []
        norm: List[Dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            content = item.get("content") if isinstance(item.get("content"), dict) else item
            title = content.get("title") or item.get("title")
            if not title:
                continue
            norm.append({
                "title": title,
                "publisher": item.get("publisher"),
                "link": item.get("link"),
                "provider_publish_time": item.get("providerPublishTime") or content.get("pubDate"),
            })
        return norm


class GDELTNewsProvider(NewsProvider):
    name = "gdelt"

    def __init__(self, cfg: Dict[str, Any], news_cfg: Dict[str, Any], cache: Optional[NewsCache] = None) -> None:
        self.enabled = bool(cfg.get("enabled", True))
        self.max_items = int(cfg.get("max_items", 15))
        self.lookback_hours = int(cfg.get("lookback_hours", 48))
        self.timeout = float(cfg.get("timeout_seconds", 8))
        self.base_url = cfg.get("base_url", "https://api.gdeltproject.org/api/v2/doc/doc")
        fresh = (news_cfg or {}).get("freshness", {})
        self.fresh_hours = float(fresh.get("fresh_hours", 24))
        self.max_age_hours = float(fresh.get("max_age_hours", 96))
        self.cache = cache

    def fetch(self, symbol, company_name=None, prefetched=None) -> List[NewsItem]:
        if not self.enabled:
            return []
        query_name = company_name or symbol.split(".")[0]
        key = f"{self.name}:{symbol}"
        articles: Optional[List[Dict[str, Any]]] = self.cache.get(key) if self.cache else None
        if articles is None:
            articles = self._query(query_name)
            if self.cache is not None:
                self.cache.put(key, articles)
        out: List[NewsItem] = []
        for art in (articles or [])[: self.max_items]:
            item = to_news_item(
                symbol=symbol,
                provider=self.name,
                title=art.get("title"),
                source=art.get("domain") or art.get("source"),
                url=art.get("url"),
                published=art.get("seendate"),
                fresh_hours=self.fresh_hours,
                max_age_hours=self.max_age_hours,
            )
            if item:
                out.append(item)
        return out

    def _query(self, query_name: str) -> List[Dict[str, Any]]:
        # Phrase-match the company; English sources; recent window.
        q = f'"{query_name}" sourcelang:english'
        params = {
            "query": q,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": str(self.max_items),
            "timespan": f"{self.lookback_hours}h",
            "sort": "DateDesc",
        }
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper-trading-demo/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = resp.read().decode("utf-8", "replace")
            data = json.loads(payload) if payload.strip() else {}
            arts = data.get("articles", []) if isinstance(data, dict) else []
            return [a for a in arts if isinstance(a, dict)]
        except Exception:
            # GDELT down / rate-limited / non-JSON -> degrade silently to no news.
            return []


class NewsAPIProvider(NewsProvider):
    name = "newsapi"
    enabled = False  # requires NEWSAPI_KEY — disabled in v1 to stay ₹0-cost

    def __init__(self, cfg: Dict[str, Any], news_cfg: Dict[str, Any]) -> None:
        self.enabled = False

    def fetch(self, symbol, company_name=None, prefetched=None) -> List[NewsItem]:
        return []


def build_news_providers(news_cfg: Dict[str, Any], cache: Optional[NewsCache] = None) -> List[NewsProvider]:
    providers_cfg = (news_cfg or {}).get("providers", {})
    providers: List[NewsProvider] = [
        YFinanceNewsProvider(providers_cfg.get("yfinance", {}), news_cfg),
        GDELTNewsProvider(providers_cfg.get("gdelt", {}), news_cfg, cache=cache),
        NewsAPIProvider(providers_cfg.get("newsapi", {}), news_cfg),
    ]
    return providers
