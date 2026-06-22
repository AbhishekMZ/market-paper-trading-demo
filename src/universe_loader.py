"""Load the equity universe from config/universe.yml.

The active list is intentionally small (8-10 names) to protect the SerpApi
free tier. Candidate names are returned too, but only for manual rotation.
"""
from __future__ import annotations

from typing import Any, Dict, List

import storage


def _clean(items: Any) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        symbol = str(it.get("symbol", "")).strip().upper()
        if not symbol:
            continue
        out.append(
            {
                "symbol": symbol,
                "exchange": str(it.get("exchange", "NSE")).strip().upper(),
                "name": str(it.get("name", symbol)).strip(),
            }
        )
    return out


def load_universe(max_active: int = 10) -> Dict[str, Any]:
    """Return {'active': [...], 'candidates': [...]} from universe.yml.

    The active list is truncated to max_active to enforce the free-tier guard
    even if the file is edited to contain more names.
    """
    cfg = storage.load_config("universe.yml")
    active = _clean(cfg.get("active_symbols"))
    candidates = _clean(cfg.get("candidate_symbols"))

    truncated = False
    if len(active) > max_active:
        active = active[:max_active]
        truncated = True

    return {
        "active": active,
        "candidates": candidates,
        "active_count": len(active),
        "candidate_count": len(candidates),
        "truncated_to_max_active": truncated,
        "max_active": max_active,
    }
