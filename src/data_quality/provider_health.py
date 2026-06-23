"""Provider-health aggregation -> the data_health.json the dashboard reads."""
from __future__ import annotations

from typing import Any, Dict, List

from utils import now_ist_iso


def build_data_health(
    provider: str,
    results: List[Dict[str, Any]],
    usable_symbols: List[str],
    rejected_symbols: List[str],
    last_run: str | None = None,
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    anomalies = [r for r in results if r.get("verdict") == "DATA_ANOMALY"]
    stale = [r for r in results if r.get("verdict") == "STALE"]
    missing_news = [r for r in results if not r.get("news_available", True)]
    health = {
        "as_of": now_ist_iso(),
        "provider": provider,
        "last_successful_run": last_run or now_ist_iso(),
        "symbols_assessed": len(results),
        "usable_symbols": len(usable_symbols),
        "rejected_symbols": len(rejected_symbols),
        "price_anomalies": len(anomalies),
        "stale_quotes": len(stale),
        "missing_news": len(missing_news),
        "anomaly_symbols": [r["symbol"] for r in anomalies],
        "rejected_symbol_list": rejected_symbols,
        "overall": _overall(len(results), len(anomalies), len(stale), len(usable_symbols)),
    }
    if extra:
        health.update(extra)
    return health


def _overall(total: int, anomalies: int, stale: int, usable: int) -> str:
    if total == 0:
        return "NO_DATA"
    if anomalies > 0:
        return "DEGRADED"
    if usable == 0:
        return "NO_USABLE_DATA"
    if stale > total / 2:
        return "STALE"
    return "HEALTHY"
