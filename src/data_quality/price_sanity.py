"""Price-sanity checks — catch bad/adjusted/inconsistent quotes before they
can produce a misleading paper trade or P&L.

The motivating bug: a position entered at one price basis (e.g. unadjusted)
marked-to-market against another basis (e.g. adjusted) showed a fake ~-42%.
These checks make entry/mark price consistency explicit and auditable.
"""
from __future__ import annotations

from typing import Any, Dict, List

from utils import minutes_since


def check_price_consistency(market_data: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compare the quote's current price against its own recent history.

    Returns a dict with the exact fields the spec asks every signal to store:
    price_source, entry_price_used, mtm_price_used, price_consistency_check.
    """
    price = market_data.get("price")
    graph = market_data.get("graph") or []
    closes = [p["price"] for p in graph if p.get("price") is not None]
    latest_close = closes[-1] if closes else None
    source = market_data.get("price_source") or market_data.get("source") or "unknown"

    reasons: List[str] = []
    checks: Dict[str, Any] = {}

    # 1) current price vs latest history close.
    divergence_pct = None
    consistency = "PASSED"
    if price is not None and latest_close:
        divergence_pct = abs(price - latest_close) / latest_close * 100.0
        checks["current_vs_history_close_pct"] = round(divergence_pct, 3)
        if divergence_pct > float(cfg.get("entry_mtm_divergence_pct", 8)):
            consistency = "FAILED"
            reasons.append(
                f"current price {price} diverges {divergence_pct:.1f}% from latest close {latest_close} "
                "(possible adjusted/unadjusted basis mismatch)."
            )
    elif price is None:
        consistency = "FAILED"
        reasons.append("no current price.")

    # 2) price must sit within the recent observed range (+ margin).
    if price is not None and len(closes) >= 3:
        lo, hi = min(closes), max(closes)
        margin = float(cfg.get("recent_range_margin_pct", 20)) / 100.0
        in_range = lo * (1 - margin) <= price <= hi * (1 + margin)
        checks["within_recent_range"] = in_range
        if not in_range:
            consistency = "FAILED"
            reasons.append(f"price {price} outside recent range [{lo:.2f}, {hi:.2f}] (+/-{margin*100:.0f}%).")

    # 3) previous_close should be present when a day-change is being used.
    prev_close_present = market_data.get("previous_close") is not None
    checks["previous_close_present"] = prev_close_present
    if not prev_close_present and market_data.get("change_pct") is not None:
        reasons.append("day change present but previous_close missing.")

    # 4) quote staleness.
    age = minutes_since(market_data.get("extracted_at"))
    if age is not None:
        checks["quote_age_minutes"] = round(age, 1)
        if age > float(cfg.get("max_quote_age_minutes", 1440)):
            reasons.append(f"quote is stale ({age:.0f} min old).")

    return {
        "price_source": source,
        "entry_price_used": price,
        "mtm_price_used": latest_close,
        "price_consistency_check": consistency,
        "checks": checks,
        "reasons": reasons,
    }
