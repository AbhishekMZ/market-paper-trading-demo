"""HistoricalContextEngine — fetch 2y bars, compute features, cache with a TTL.

Fetches trailing daily history (default 2y) for each symbol + the benchmark via
the injected MarketDataProvider, computes features (context.features), and caches
the result as committed JSON so the 3 daily checkpoints reuse one fetch. The
cache lives under data/state and is committed by the analyze workflow.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

import storage
from context.features import benchmark_trailing, close_series, compute_features
from utils import now_ist_iso


def _hours_between(then_iso: str, now_iso: str) -> Optional[float]:
    """Hours from then_iso to now_iso, or None if either is unparseable."""
    try:
        t0 = dt.datetime.fromisoformat(then_iso)
        t1 = dt.datetime.fromisoformat(now_iso)
        return (t1 - t0).total_seconds() / 3600.0
    except (TypeError, ValueError):
        return None


class HistoricalContextEngine:
    def __init__(self, cfg, provider, usage=None, cache_filename="historical_context.json"):
        cfg = cfg or {}
        self.cfg = cfg
        self.enabled = bool(cfg.get("enabled", True))
        self.provider = provider
        self.usage = usage
        self.period = str(cfg.get("lookback_period", "2y"))
        self.interval = str(cfg.get("interval", "1d"))
        self.ttl_hours = float(cfg.get("refresh_ttl_hours", 20))
        self.benchmark_symbol = str(cfg.get("benchmark_symbol", "^NSEI"))
        self.cache_filename = cache_filename

    def _cache_path(self) -> str:
        return storage.state_file(self.cache_filename)

    def load(self) -> Dict[str, Any]:
        data = storage.read_json(self._cache_path(), {})
        return data if isinstance(data, dict) else {}

    def _is_fresh(self, cached: Dict[str, Any], now_iso: str) -> bool:
        as_of = cached.get("as_of") if isinstance(cached, dict) else None
        if not as_of:
            return False
        age = _hours_between(as_of, now_iso)
        return age is not None and 0 <= age < self.ttl_hours

    def refresh_if_stale(self, symbols: List[str], now_iso: Optional[str] = None) -> Dict[str, Any]:
        now_iso = now_iso or now_ist_iso()
        if not self.enabled:
            return {"as_of": now_iso, "ttl_hours": self.ttl_hours, "symbols": {}, "disabled": True}
        cached = self.load()
        if self._is_fresh(cached, now_iso):
            bench = cached.get("benchmark") if isinstance(cached, dict) else None
            if not (isinstance(bench, dict) and bench.get("return_20d_pct") is not None):
                return self._attach_benchmark(cached, now_iso)
            return cached
        return self._refresh(symbols, now_iso)

    def _attach_benchmark(self, cached: Dict[str, Any], now_iso: str) -> Dict[str, Any]:
        """Fill the index block on an otherwise-fresh cache. One benchmark fetch."""
        try:
            closes = close_series(self._fetch_bars(self.benchmark_symbol))
            cached = dict(cached or {})
            cached["benchmark"] = benchmark_trailing(closes)
            storage.write_json(self._cache_path(), cached)
        except Exception:
            return cached if isinstance(cached, dict) else {"as_of": now_iso, "symbols": {}}
        return cached

    def _fetch_bars(self, symbol: str) -> List[Any]:
        snap = self.provider.get_snapshot(symbol, period=self.period, interval=self.interval)
        if self.usage is not None:
            try:
                self.usage.record()
            except Exception:
                pass
        return list(getattr(snap, "history", []) or [])

    def _refresh(self, symbols: List[str], now_iso: str) -> Dict[str, Any]:
        bench_closes = close_series(self._fetch_bars(self.benchmark_symbol))
        out_symbols: Dict[str, Any] = {}
        for sym in symbols:
            try:
                bars = self._fetch_bars(sym)
                feats = compute_features(bars, bench_closes=bench_closes, cfg=self.cfg)
                feats["as_of"] = now_iso
                out_symbols[sym] = feats
            except Exception as exc:
                out_symbols[sym] = {"coverage": "insufficient", "n_bars": 0,
                                    "as_of": now_iso, "error": str(exc)}
        snapshot = {
            "as_of": now_iso,
            "ttl_hours": self.ttl_hours,
            "benchmark": benchmark_trailing(bench_closes),
            "symbols": out_symbols,
        }
        storage.write_json(self._cache_path(), snapshot)
        storage.append_audit({"event": "HISTORICAL_CONTEXT_REFRESH",
                              "symbols": len(out_symbols), "as_of": now_iso})
        return snapshot
