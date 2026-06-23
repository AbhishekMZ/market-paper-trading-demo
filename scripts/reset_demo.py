"""Reset the fake-money paper-trading demo to a clean state.

Wipes portfolio, budget, trade/signal history, audit log, approvals, usage, and
data-quality artifacts back to a fresh ₹0-position start. Paper-only — touches
nothing real.

REQUIRES an explicit confirmation token to prevent accidents:
    python scripts/reset_demo.py --confirm RESET_PAPER_DEMO
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import static_exporter  # noqa: E402
import storage  # noqa: E402
from utils import month_ist_str, now_ist_iso, today_ist_str, write_json  # noqa: E402

CONFIRM_TOKEN = "RESET_PAPER_DEMO"


def reset() -> None:
    storage.ensure_dirs()
    settings = storage.load_config("settings.yml")
    cap = settings.get("capital", {})
    starting = float(cap.get("monthly_fake_capital", 10000))

    # Clean portfolio (no positions).
    storage.save_state("portfolio", {
        "as_of": now_ist_iso(), "starting_capital": starting, "monthly_capital": starting,
        "cash": starting, "holdings_value": 0.0, "total_value": starting,
        "realized_pnl": 0.0, "unrealized_pnl": 0.0, "positions": [], "closed_positions": [],
        "peak_total_value": starting, "max_drawdown_pct": 0.0,
    })
    storage.save_state("monthly_budget", {
        "month": month_ist_str(), "monthly_capital": starting, "capital_deployed": 0.0,
        "capital_remaining": starting, "buys_this_month": 0,
        "max_buys_per_month": int(cap.get("max_buys_per_month", 5)), "realized_pnl_month": 0.0,
    })
    for name, empty in (("trade_history", []), ("signal_history", []), ("approvals", [])):
        storage.save_state(name, empty)
    storage.save_state("execution_state", {
        "mode": "paper", "broker_adapter": "paper", "live_trading_enabled": False,
        "angel_one_enabled": False, "require_manual_approval": True, "allow_real_orders": False,
        "kill_switch": False, "buys_today": 0, "buy_date": today_ist_str(), "last_run": None,
    })
    storage.save_state("api_usage", {
        "month": month_ist_str(), "calls_total": 0, "daily": {}, "warnings": [],
        "provider": settings.get("market_data", {}).get("provider", "yfinance"),
        "budget_enabled": False, "calls_today": 0, "last_updated": now_ist_iso(),
    })
    # Truncate the audit log and DQ / news artifacts.
    open(storage.AUDIT_LOG_PATH, "w", encoding="utf-8").close()
    artifacts = (
        "data_quality_incidents.json", "data_health.json", "strategy_evaluation.json",
        "news_assessments.json", "news_items.json", "news_alerts.json", "news_health.json",
    )
    for f in artifacts:
        for p in (storage.report_file(f), storage.public_file(f)):
            if os.path.exists(p):
                os.remove(p)
    write_json(storage.state_file("dq_source_log.json"), {})
    write_json(storage.state_file("news_cache.json"), {})
    storage.append_audit({"event": "DEMO_RESET", "message": "Paper demo reset to clean state.",
                          "starting_capital": starting})
    static_exporter.export_all()
    print(f"✓ Paper demo reset. Cash ₹{starting:,.0f}, 0 positions, histories cleared.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset the paper-trading demo (paper-only).")
    parser.add_argument("--confirm", default="", help=f"must equal {CONFIRM_TOKEN}")
    args = parser.parse_args()
    if args.confirm != CONFIRM_TOKEN:
        print(f"Refusing to reset: pass --confirm {CONFIRM_TOKEN}", file=sys.stderr)
        return 2
    reset()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
