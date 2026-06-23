"""Single source of truth for file paths and JSON/YAML state persistence.

Everything that touches disk goes through here so paths stay consistent
across the engines, the report generator, and the static exporter.

State layout (all plain JSON/JSONL — no database in v1):
    data/state/portfolio.json         current fake portfolio
    data/state/monthly_budget.json    monthly capital + buy counters
    data/state/trade_history.json     list of executed paper trades
    data/state/signal_history.json    list of generated signals
    data/state/api_usage.json         SerpApi call counters / budget
    data/state/approvals.json         manual-approval queue (future use)
    data/state/execution_state.json   live mode / adapter / kill switch
    data/state/audit_log.jsonl        append-only audit trail
"""
from __future__ import annotations

import os
from typing import Any

from utils import append_jsonl, load_yaml, now_ist_iso, read_json, read_jsonl, write_json

# repo root = parent of src/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DIR = os.path.join(ROOT, "config")
DATA_DIR = os.path.join(ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
STATE_DIR = os.path.join(DATA_DIR, "state")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
DAILY_REPORTS_DIR = os.path.join(REPORTS_DIR, "daily")
PUBLIC_DATA_DIR = os.path.join(ROOT, "public", "data")

AUDIT_LOG_PATH = os.path.join(STATE_DIR, "audit_log.jsonl")

STATE_FILES = {
    "portfolio": "portfolio.json",
    "monthly_budget": "monthly_budget.json",
    "trade_history": "trade_history.json",
    "signal_history": "signal_history.json",
    "api_usage": "api_usage.json",
    "approvals": "approvals.json",
    "execution_state": "execution_state.json",
}


def ensure_dirs() -> None:
    for d in (RAW_DIR, PROCESSED_DIR, STATE_DIR, REPORTS_DIR, DAILY_REPORTS_DIR, PUBLIC_DATA_DIR):
        os.makedirs(d, exist_ok=True)


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
def config_path(name: str) -> str:
    return os.path.join(CONFIG_DIR, name)


def load_config(name: str) -> dict:
    """Load one config file, e.g. load_config('settings.yml')."""
    return load_yaml(config_path(name))


def load_all_configs() -> dict:
    """Load every config file into one dict keyed by base name."""
    return {
        "settings": load_config("settings.yml"),
        "broker": load_config("broker.yml"),
        "risk": load_config("risk.yml"),
        "scoring": load_config("scoring.yml"),
        "universe": load_config("universe.yml"),
        "costs": load_config("costs.yml"),
        "news": _load_optional("news.yml"),
        "evaluation": _load_optional("evaluation.yml"),
        "observation": _load_optional("observation.yml"),
    }


def _load_optional(name: str) -> dict:
    """Load a config that may be absent on older checkouts (returns {} if missing)."""
    try:
        return load_yaml(config_path(name))
    except FileNotFoundError:
        return {}


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
def state_path(name: str) -> str:
    if name not in STATE_FILES:
        raise KeyError(f"Unknown state file: {name}")
    return os.path.join(STATE_DIR, STATE_FILES[name])


def state_file(filename: str) -> str:
    """Path for an ad-hoc state file not in the fixed STATE_FILES map."""
    return os.path.join(STATE_DIR, filename)


def report_file(filename: str) -> str:
    return os.path.join(REPORTS_DIR, filename)


def public_file(filename: str) -> str:
    return os.path.join(PUBLIC_DATA_DIR, filename)


def load_state(name: str, default: Any = None) -> Any:
    return read_json(state_path(name), default if default is not None else {})


def save_state(name: str, data: Any) -> None:
    write_json(state_path(name), data)


# --------------------------------------------------------------------------- #
# Audit log (append-only JSONL)
# --------------------------------------------------------------------------- #
def append_audit(record: dict) -> dict:
    """Append a single audit record. Always stamps a timestamp."""
    record = {"ts": now_ist_iso(), **record}
    append_jsonl(AUDIT_LOG_PATH, record)
    return record


def read_audit(limit: int | None = None) -> list:
    records = read_jsonl(AUDIT_LOG_PATH)
    if limit is not None:
        return records[-limit:]
    return records
