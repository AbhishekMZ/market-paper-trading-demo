"""Scheduler — decide which checkpoint a run represents.

Supports:
  * Manual run            (CLI / workflow_dispatch)
  * Checkpoint run        (matched to the nearest configured checkpoint)
  * End-of-day report     (after the last checkpoint)
  * GitHub Actions mode   (cron passes --checkpoint or we infer from time)

The system does NOT scan continuously — it acts only at discrete checkpoints.
NSE holidays (config/nse_holidays.yml) are skipped unless --force / --manual.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Set

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


def _holiday_dates() -> Set[str]:
    """Load YYYY-MM-DD closed dates from config/nse_holidays.yml (best-effort)."""
    try:
        import storage  # local import — available when running from src/

        cfg = storage.load_config("nse_holidays.yml") or {}
        out: Set[str] = set()
        for row in cfg.get("nse_holidays") or []:
            if isinstance(row, dict) and row.get("date"):
                out.add(str(row["date"]).strip()[:10])
            elif isinstance(row, str):
                out.add(row.strip()[:10])
        return out
    except Exception:
        return set()


def is_nse_holiday(day: Optional[dt.date] = None) -> bool:
    """True if *day* (IST today by default) is on the NSE holiday list."""
    d = day or now_ist().date()
    return d.isoformat() in _holiday_dates()


def is_trading_day(settings: Dict[str, Any] = None) -> bool:
    """Weekdays that are not on the NSE holiday calendar."""
    if not is_weekday():
        return False
    return not is_nse_holiday()
