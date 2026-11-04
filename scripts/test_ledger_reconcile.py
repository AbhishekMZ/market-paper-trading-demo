"""Offline test: missing filled buys are restored onto the portfolio."""
from __future__ import annotations

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import storage  # noqa: E402

storage.redirect_runtime_dirs(tempfile.mkdtemp(prefix="mmg_ledger_"))
from ledger_reconcile import reconcile_portfolio_from_trades  # noqa: E402


def main() -> int:
    storage.save_state("portfolio", {
        "starting_capital": 10000.0,
        "cash": 8.41,
        "positions": [{"symbol": "ITC.NS", "quantity": 3}],
        "closed_positions": [{"symbol": "COLPAL.NS"}],
    })
    storage.save_state("trade_history", [
        {"status": "FILLED", "side": "BUY", "symbol": "ITC.NS", "quantity": 3, "price": 100.0, "timestamp": "2026-06-23T11:00:00+05:30"},
        {"status": "FILLED", "side": "BUY", "symbol": "AAA.NS", "quantity": 2, "price": 50.0, "timestamp": "2026-10-14T16:00:00+05:30"},
        {"status": "REJECTED", "side": "BUY", "symbol": "BBB.NS", "quantity": 9, "price": 10.0, "timestamp": "2026-10-14T16:01:00+05:30"},
    ])
    note = reconcile_portfolio_from_trades()
    assert note and "AAA.NS" in note
    pf = storage.load_state("portfolio", {})
    held = {p["symbol"]: p["quantity"] for p in pf["positions"]}
    assert held == {"ITC.NS": 3, "AAA.NS": 2}, held
    assert abs(pf["cash"] - (10000 - 300 - 100)) < 0.01, pf["cash"]
    assert reconcile_portfolio_from_trades() is None
    print("OK: ledger reconcile restores missing fills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
