"""Scheduler — decide which checkpoint a run represents.

Supports:
  * Manual run            (CLI / workflow_dispatch)
  * Checkpoint run        (matched to the nearest configured checkpoint)
  * End-of-day report     (after the last checkpoint)
  * GitHub Actions mode   (cron passes --checkpoint or we infer from time)

The system does NOT scan continuously — it acts only at discrete checkpoints.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from utils import IST, is_weekday, now_ist


def _checkpoints(settings: Dict[str, Any]) -> List[Dict[str, Any]]:
    cps = settings.get("checkpoints", [])
    md = settings.get("market_data", {})
    if md.get("single_checkpoint_mode"):
        return cps[:1]
    max_cp = int(md.get("max_checkpoints_per_day", 3))
    return cps[:max_cp]


def resolve_checkpoint(settings: Dict[str, Any], forced: Optional[str] = None) -> Dict[str, Any]:
    """Return {'id', 'label', 'is_last', 'matched_by'} for this run."""
    cps = _checkpoints(settings)
    if not cps:
        return {"id": "manual", "label": "Manual", "is_last": True, "matched_by": "fallback"}

    if forced and forced not in ("auto", "", None):
        match = next((c for c in cps if c["id"] == forced), None)
        if match:
            return {"id": match["id"], "label": match.get("label", match["id"]),
                    "is_last": match["id"] == cps[-1]["id"], "matched_by": "forced"}
        # Manual/EOD pseudo-checkpoints.
        if forced in ("manual", "eod"):
            return {"id": forced, "label": forced.upper(), "is_last": True, "matched_by": "forced"}
        return {"id": forced, "label": forced, "is_last": True, "matched_by": "forced"}

    # Infer from the current IST time: pick the most recent past checkpoint.
    now = now_ist()
    chosen = cps[0]
    for c in cps:
        hh, mm = [int(x) for x in str(c["time_ist"]).split(":")]
        cp_time = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if now >= cp_time:
            chosen = c
    return {"id": chosen["id"], "label": chosen.get("label", chosen["id"]),
            "is_last": chosen["id"] == cps[-1]["id"], "matched_by": "time"}


def is_trading_day(settings: Dict[str, Any]) -> bool:
    # Weekdays only. (NSE holidays are not modeled in v1; a holiday simply
    # produces a low-data run that declines to trade — which is safe.)
    return is_weekday()
