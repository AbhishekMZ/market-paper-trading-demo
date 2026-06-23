"""Generate SAMPLE paper-trading data by driving the REAL pipeline.

This does NOT hit the network. It monkeypatches the market-data provider with
deterministic, clearly-synthetic snapshots so the full engine (regime -> hybrid
strategies -> risk -> paper broker -> reports -> export) runs end to end and
produces realistic sample state, reports, and a sample paper trade.

Run:  python scripts/seed_sample_data.py
The generated files are SAMPLE/demo data — deterministic and safe to commit so
the dashboard has something to show before the first live run.
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

os.environ.setdefault("EMAIL_ENABLED", "false")

from market_data.base import MarketQuote, MarketSnapshot, PriceBar  # noqa: E402
from utils import now_ist_iso  # noqa: E402

# Deterministic per-symbol profiles. "strong" => buy-worthy uptrend.
PROFILES = {
    "ITC.NS":        ("strong", 480.0,  2.5),   # strong AND affordable -> a paper BUY
    "RELIANCE.NS":   ("strong", 2900.0, 2.3),   # strong but price > ₹2000 cap -> no buy
    "HDFCBANK.NS":   ("moderate", 1650.0, 0.4),
    "INFY.NS":       ("moderate", 1550.0, 0.6),
    "ICICIBANK.NS":  ("moderate", 1200.0, 0.3),
    "SBIN.NS":       ("weak", 820.0, -3.6),     # weak -> DO_NOT_BUY / HIGH_RISK
    "LT.NS":         ("moderate", 3600.0, 0.5),
    "BHARTIARTL.NS": ("moderate", 1400.0, 0.2),
    "AXISBANK.NS":   ("moderate", 1100.0, 0.1),
    "TCS.NS":        ("weak", 3900.0, -2.4),
    # Benchmarks -> clearly positive => strong RISK_ON regime.
    "^NSEI":         ("bench", 24800.0, 1.8),
    "^NSEBANK":      ("bench", 55200.0, 1.7),
}

SAMPLE_NEWS = {
    # Positive news on the buy candidate — informational only; never forces a buy.
    "ITC.NS": [{"title": "ITC reports strong results; margin improvement and debt reduction noted",
                "publisher": "SAMPLE", "link": "", "provider_publish_time": 0, "type": "STORY"}],
    # CRITICAL adverse news on a weak name — demonstrates the news panels + that
    # news BLOCKS buys (this symbol is not a buy candidate, so no trade is affected).
    "SBIN.NS": [{"title": "SAMPLE: SBIN faces SEBI fraud probe; forensic audit ordered",
                 "publisher": "SAMPLE", "link": "", "provider_publish_time": 0, "type": "STORY"}],
}


# Simulated "day" offset for multi-run seeding (--days). Each extra day drifts
# prices so the Decision Quality Engine sees real forward returns: strong names
# trend up, weak names down, the index up. Default 0 = single static snapshot.
DAY = 0
DAILY_DRIFT_PCT = {"strong": 1.2, "moderate": 0.1, "weak": -1.0, "bench": 0.5}


def _bars(base: float, total_change_pct: float, n: int = 22):
    end = base * (1 + total_change_pct / 100.0)
    bars = []
    for i in range(n):
        frac = i / (n - 1)
        wiggle = ((i % 3) - 1) * base * 0.0008
        close = round(base + (end - base) * frac + wiggle, 2)
        bars.append(PriceBar(timestamp=f"2026-06-{i+1:02d}T00:00:00+05:30",
                             open=close, high=round(close * 1.004, 2),
                             low=round(close * 0.996, 2), close=close, volume=1000000 + i))
    return bars


def synthetic_get_snapshot(self, symbol, period="1mo", interval="1d"):
    profile = PROFILES.get(symbol)
    if profile is None:
        return self._empty_snapshot(symbol, ["no sample profile"])
    kind, base, change_pct = profile
    # Apply the simulated-day drift so successive seed runs produce a price path.
    base = round(base * (1 + DAILY_DRIFT_PCT.get(kind, 0.0) / 100.0 * DAY), 2)
    series_change = {"strong": 6.0, "moderate": 0.8, "weak": -5.0, "bench": change_pct * 2}[kind]
    bars = _bars(base, series_change)
    price = bars[-1].close
    prev = round(price / (1 + change_pct / 100.0), 2)
    quote = MarketQuote(
        symbol=symbol, name=symbol, currency="INR", exchange="NSE",
        current_price=price, previous_close=prev,
        day_change=round(price - prev, 2), day_change_pct=change_pct,
        timestamp=now_ist_iso(), provider="SAMPLE_SYNTHETIC", raw={},
    )
    news = SAMPLE_NEWS.get(symbol, [])
    return MarketSnapshot(
        symbol=symbol, quote=quote, history=bars, news=news,
        data_quality={"provider": "SAMPLE_SYNTHETIC", "symbol": symbol, "has_quote": True,
                      "history_bars": len(bars), "has_news": bool(news), "errors": [], "is_usable": True},
    )


def main() -> int:
    # Patch the provider class BEFORE importing the orchestrator's run.
    from market_data.yahoo_finance_provider import YahooFinanceProvider
    YahooFinanceProvider.get_snapshot = synthetic_get_snapshot

    # Honor the "no network" contract: stub the GDELT news provider so the news
    # overlay runs deterministically against SAMPLE_NEWS only (no live fetch).
    import news.providers as news_providers
    news_providers.GDELTNewsProvider._query = lambda self, query_name: []

    import main as orchestrator  # noqa: E402

    parser = argparse.ArgumentParser(description="Seed SAMPLE paper-trading data (offline).")
    parser.add_argument("--days", type=int, default=1,
                        help="simulate N successive runs with price drift (populates forward returns/benchmark)")
    cli = parser.parse_args()

    args = argparse.Namespace(checkpoint="close", manual=True, eod=True, monthly=True, force=True,
                              observe=False, observe_only=False, focused_symbol=None,
                              escalation_report=False, no_action=False)
    print(f"=== Seeding SAMPLE data through the real pipeline ({cli.days} simulated day(s)) ===")
    rc = 0
    for d in range(max(1, cli.days)):
        globals()["DAY"] = d  # synthetic_get_snapshot reads this at call time
        rc = orchestrator.run(args)
        if rc != 0:
            break
    print(f"=== Done (exit {rc}). Sample data written to data/ and public/data/. ===")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
