"""Anomaly detection — extreme moves, split/CA discontinuities, source flips.

Deterministic, rule-based. Flags conditions that usually mean the *data* is
wrong rather than the market having genuinely moved, so the strategy layer can
refuse to act on it.
"""
from __future__ import annotations

from typing import Any, Dict, List


def detect_anomalies(
    market_data: Dict[str, Any], cfg: Dict[str, Any], prior_source: str | None = None
) -> Dict[str, Any]:
    flags: List[str] = []
    reasons: List[str] = []
    graph = market_data.get("graph") or []
    closes = [p["price"] for p in graph if p.get("price") is not None]
    change_pct = market_data.get("change_pct")
    news_available = bool(market_data.get("news_available"))

    # 1) Extreme one-day move without a news / corporate-action flag.
    extreme = float(cfg.get("extreme_move_pct", 20))
    if change_pct is not None and abs(change_pct) >= extreme and not news_available:
        flags.append("extreme_move_unexplained")
        reasons.append(f"day move {change_pct:.1f}% >= {extreme:.0f}% with no news/corporate-action flag.")

    # 2) Split / corporate-action discontinuity in the history series.
    split_gap = float(cfg.get("split_gap_pct", 25))
    max_gap = 0.0
    for a, b in zip(closes, closes[1:]):
        if a:
            gap = abs(b - a) / a * 100.0
            max_gap = max(max_gap, gap)
    if max_gap >= split_gap:
        flags.append("split_or_ca_discontinuity")
        reasons.append(f"consecutive close gap {max_gap:.1f}% >= {split_gap:.0f}% (suspected split/corporate action).")

    # 3) Quote source changed within the day (basis flip risk).
    current_source = market_data.get("price_source") or market_data.get("source")
    if prior_source and current_source and prior_source != current_source:
        flags.append("quote_source_changed")
        reasons.append(f"price source changed today: {prior_source} -> {current_source}.")

    return {"anomaly_flags": flags, "anomaly_reasons": reasons, "max_close_gap_pct": round(max_gap, 2)}
