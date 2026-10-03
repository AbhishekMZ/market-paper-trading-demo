"""Offline tests for config/universe.yml + nifty500.csv loading.

Run:  py -3 scripts/test_universe_loader.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import storage  # noqa: E402
from universe_loader import _resolve_csv_source, load_universe  # noqa: E402


def test_csv_is_active_source_for_repo_config() -> None:
    max_active = 500
    u = load_universe(max_active=max_active)
    assert u["source_used"] == "csv", u
    assert u["source_file"] == "nifty500.csv", u
    assert u["symbols_available"] >= 500, u["symbols_available"]
    assert u["symbols_requested"] == min(u["symbols_available"], max_active)
    assert u["active_count"] == u["symbols_requested"]
    assert u["active"][0]["symbol"].endswith(".NS")
    assert not u["source_fallback"]
    print(f"[ok] repo CSV source: requested={u['symbols_requested']} "
          f"available={u['symbols_available']} source={u['source_used']}")


def test_respects_max_symbols_per_run() -> None:
    u = load_universe(max_active=10)
    assert u["source_used"] == "csv", u
    assert u["symbols_requested"] == 10
    assert u["active_count"] == 10
    assert u["partial_scan"] is True
    assert u["truncated_to_max_active"] is True
    assert u["symbols_available"] > 10
    print(f"[ok] max_active=10 truncates: available={u['symbols_available']} "
          f"requested={u['symbols_requested']} partial={u['partial_scan']}")


def test_string_active_source_shorthand() -> None:
    resolved = _resolve_csv_source("nifty500.csv")
    assert resolved is not None
    assert resolved["type"] == "csv"
    assert resolved["csv_file"] == "nifty500.csv"
    print("[ok] string active_source shorthand resolves to csv")


def test_missing_csv_falls_back_to_inline() -> None:
    """If the configured CSV is missing, inline active_symbols is used."""
    cfg = storage.load_config("universe.yml")
    inline_n = len(cfg.get("active_symbols") or [])
    assert inline_n > 0

    # Point at a non-existent CSV under config/ without rewriting universe.yml.
    missing = {
        "type": "csv",
        "csv_file": "__does_not_exist_universe_test__.csv",
        "symbol_column": "Symbol",
        "name_column": "Company Name",
        "symbol_suffix": ".NS",
        "exchange": "NSE",
    }
    # Exercise the private loader path via a temp universe.yml overlay.
    original_load = storage.load_config

    def fake_load(name: str):
        data = original_load(name)
        if name == "universe.yml":
            data = dict(data)
            data["active_source"] = missing
        return data

    storage.load_config = fake_load  # type: ignore
    try:
        u = load_universe(max_active=500)
        assert u["source_used"] == "active_symbols", u
        assert u["source_fallback"] is True
        assert u["symbols_requested"] == inline_n
        print(f"[ok] missing CSV falls back to active_symbols ({inline_n})")
    finally:
        storage.load_config = original_load  # type: ignore


def main() -> int:
    # Sanity: bundled CSV is present for the happy-path tests.
    csv_path = Path(storage.config_path("nifty500.csv"))
    assert csv_path.is_file(), f"expected {csv_path}"

    test_string_active_source_shorthand()
    test_csv_is_active_source_for_repo_config()
    test_respects_max_symbols_per_run()
    test_missing_csv_falls_back_to_inline()
    print("[ok] universe_loader tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
