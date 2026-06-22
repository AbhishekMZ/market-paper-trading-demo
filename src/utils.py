"""Shared helpers: time (Asia/Kolkata), YAML/JSON loading, formatting, IDs.

Low-level module. It must NOT import other project modules (avoids cycles).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import uuid
from typing import Any, Optional

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

import yaml

IST = ZoneInfo("Asia/Kolkata") if ZoneInfo else dt.timezone(dt.timedelta(hours=5, minutes=30))


# --------------------------------------------------------------------------- #
# Time helpers (always Asia/Kolkata)
# --------------------------------------------------------------------------- #
def now_ist() -> dt.datetime:
    """Timezone-aware 'now' in IST."""
    return dt.datetime.now(IST)


def now_ist_iso() -> str:
    return now_ist().isoformat(timespec="seconds")


def today_ist_str() -> str:
    return now_ist().strftime("%Y-%m-%d")


def month_ist_str() -> str:
    return now_ist().strftime("%Y-%m")


def is_weekday(d: Optional[dt.datetime] = None) -> bool:
    d = d or now_ist()
    return d.weekday() < 5  # Mon-Fri


def parse_iso(value: str) -> Optional[dt.datetime]:
    try:
        return dt.datetime.fromisoformat(value)
    except Exception:
        return None


def minutes_since(iso_value: Optional[str]) -> Optional[float]:
    """Minutes elapsed since an ISO timestamp, or None if unparseable."""
    if not iso_value:
        return None
    parsed = parse_iso(iso_value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=IST)
    return (now_ist() - parsed).total_seconds() / 60.0


# --------------------------------------------------------------------------- #
# IO helpers
# --------------------------------------------------------------------------- #
def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def read_json(path: str, default: Any = None) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path: str, data: Any) -> None:
    """Atomic JSON write (temp file + os.replace)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
    os.replace(tmp, path)


def append_jsonl(path: str, record: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def read_jsonl(path: str) -> list:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


# --------------------------------------------------------------------------- #
# Formatting / misc
# --------------------------------------------------------------------------- #
def gen_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def money(amount: float, symbol: str = "₹") -> str:
    try:
        return f"{symbol}{amount:,.2f}"
    except (TypeError, ValueError):
        return f"{symbol}0.00"


def pct(value: float) -> str:
    try:
        return f"{value:+.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
