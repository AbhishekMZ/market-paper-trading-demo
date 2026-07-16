"""Load the equity universe from config/universe.yml.

The active list can be sourced either from an inline ``active_symbols`` list in
config/universe.yml (small, hand-curated) OR from a bundled CSV (e.g. the full
NIFTY 500 constituents). Configure the CSV source under ``active_source`` in
universe.yml. Candidate names are returned too, but only for manual rotation.
"""
from __future__ import annotations

import csv
import os
from typing import Any, Dict, List

import storage


def _load_csv_symbols(source: Dict[str, Any]) -> List[Dict[str, str]]:
    """Build an active list from a bundled CSV (e.g. NIFTY 500 constituents).

    Expected config shape under universe.yml -> active_source:
        type: csv
        csv_file: nifty500.csv          # relative to config/ dir
        symbol_column: Symbol
        name_column: Company Name
        symbol_suffix: ".NS"            # appended for yfinance (NSE)
        exchange: NSE
    """
    csv_file = str(source.get("csv_file", "")).strip()
    if not csv_file:
        return []
    path = csv_file if os.path.isabs(csv_file) else storage.config_path(csv_file)
    if not os.path.exists(path):
        return []

    symbol_col = source.get("symbol_column", "Symbol")
    name_col = source.get("name_column", "Company Name")
    suffix = str(source.get("symbol_suffix", ".NS"))
    exchange = str(source.get("exchange", "NSE")).strip().upper()

    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            base = str(row.get(symbol_col, "")).strip().upper()
            if not base:
                continue
            symbol = base if base.endswith(suffix) else f"{base}{suffix}"
            rows.append(
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "name": str(row.get(name_col, base)).strip() or base,
                }
            )
    return _clean(rows)


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

    # Prefer a CSV source (e.g. the bundled NIFTY 500 list) when configured and
    # it yields symbols; otherwise fall back to the inline active_symbols list.
    source = cfg.get("active_source") or {}
    active: List[Dict[str, str]] = []
    if str(source.get("type", "")).strip().lower() == "csv":
        active = _load_csv_symbols(source)
    if not active:
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
