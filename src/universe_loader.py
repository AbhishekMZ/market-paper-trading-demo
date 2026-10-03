"""Load the equity universe from config/universe.yml.

The active list can be sourced either from an inline ``active_symbols`` list in
config/universe.yml (small, hand-curated) OR from a bundled CSV (e.g. the full
NIFTY 500 constituents). Configure the CSV source under ``active_source`` in
universe.yml. Candidate names are returned too, but only for manual rotation.
"""
from __future__ import annotations

import csv
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import storage


def _resolve_csv_source(source: Any) -> Optional[Dict[str, Any]]:
    """Normalize ``active_source`` to a CSV config dict, or None if not CSV.

    Accepted shapes:
      active_source: nifty500.csv
      active_source: { type: csv, csv_file: nifty500.csv, ... }
    """
    if isinstance(source, str):
        path = source.strip()
        if not path:
            return None
        return {
            "type": "csv",
            "csv_file": path,
            "symbol_column": "Symbol",
            "name_column": "Company Name",
            "symbol_suffix": ".NS",
            "exchange": "NSE",
        }
    if not isinstance(source, dict):
        return None
    src_type = str(source.get("type", "")).strip().lower()
    csv_file = str(source.get("csv_file", "")).strip()
    # Prefer explicit type: csv; also accept a bare csv_file with no type.
    if src_type == "csv" or (not src_type and csv_file.lower().endswith(".csv")):
        out = dict(source)
        out["type"] = "csv"
        if csv_file:
            out["csv_file"] = csv_file
        return out
    return None


def _load_csv_symbols(source: Dict[str, Any]) -> Tuple[List[Dict[str, str]], str]:
    """Build an active list from a bundled CSV (e.g. NIFTY 500 constituents).

    Returns (rows, detail) where detail is empty on success, else a short reason.
    """
    csv_file = str(source.get("csv_file", "")).strip()
    if not csv_file:
        return [], "active_source.csv_file is empty"
    path = csv_file if os.path.isabs(csv_file) else storage.config_path(csv_file)
    if not os.path.exists(path):
        return [], f"CSV not found: {path}"

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
    cleaned = _clean(rows)
    if not cleaned:
        return [], f"CSV yielded 0 symbols: {path}"
    return cleaned, ""


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
    """Return active/candidate symbols from universe.yml.

    When ``active_source`` points at a CSV (e.g. nifty500.csv), that list is the
    real active universe. The inline ``active_symbols`` list is only a fallback
    if the CSV cannot be loaded. The active list is truncated to ``max_active``
    (typically ``market_data.max_symbols_per_run`` from settings.yml).
    """
    cfg = storage.load_config("universe.yml")
    raw_source = cfg.get("active_source")
    csv_source = _resolve_csv_source(raw_source)

    active: List[Dict[str, str]] = []
    source_used = "active_symbols"
    source_file = ""
    source_fallback = False
    fallback_reason = ""

    if csv_source is not None:
        source_file = str(csv_source.get("csv_file", "")).strip()
        active, err = _load_csv_symbols(csv_source)
        if active:
            source_used = "csv"
        else:
            source_fallback = True
            fallback_reason = err or "CSV source produced no symbols"
            print(
                f"[universe] WARNING: active_source CSV failed ({fallback_reason}); "
                f"falling back to inline active_symbols",
                file=sys.stderr,
            )

    if not active:
        active = _clean(cfg.get("active_symbols"))
        source_used = "active_symbols"
        if csv_source is None and raw_source not in (None, "", {}, []):
            print(
                f"[universe] WARNING: active_source={raw_source!r} was not recognized as CSV; "
                f"using inline active_symbols ({len(active)})",
                file=sys.stderr,
            )

    candidates = _clean(cfg.get("candidate_symbols"))
    symbols_available = len(active)

    truncated = False
    if len(active) > max_active:
        active = active[:max_active]
        truncated = True

    return {
        "active": active,
        "candidates": candidates,
        "active_count": len(active),
        "candidate_count": len(candidates),
        "symbols_available": symbols_available,
        "symbols_requested": len(active),
        "truncated_to_max_active": truncated,
        "partial_scan": truncated,
        "max_active": max_active,
        "source_used": source_used,
        "source_file": source_file,
        "source_fallback": source_fallback,
        "fallback_reason": fallback_reason,
    }
