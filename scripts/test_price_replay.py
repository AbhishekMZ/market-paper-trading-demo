"""Tests for the price-only historical replay (no look-ahead, sane aggregation).

Run:  python scripts/test_price_replay.py
No internet required — uses a deterministic in-memory provider.
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from backtesting.price_replay import PriceOnlyReplay  # noqa: E402


class _Bar:
    def __init__(self, timestamp: str, close: float) -> None:
        self.timestamp = timestamp
        self.close = close


class _Snap:
    def __init__(self, bars):
        self.history = bars


class _FakeProvider:
    """Returns a deterministic rising-with-noise series for any symbol."""

    def __init__(self, n: int = 120):
        self.n = n

    def get_snapshot(self, symbol, period="2y", interval="1d"):
        bars = []
        price = 100.0
        for i in range(self.n):
            # gentle uptrend + deterministic wiggle (symbol-seeded, no randomness)
            price *= 1.0 + 0.002 + 0.01 * math.sin(i / 3.0 + len(symbol))
            bars.append(_Bar(f"2025-01-{(i % 27) + 1:02d}T00:00:00+05:30", round(price, 2)))
        # give each date a unique key so benchmark alignment works
        for i, b in enumerate(bars):
            b.timestamp = f"2025-{(i // 27) + 1:02d}-{(i % 27) + 1:02d}T00:00:00+05:30"
        return _Snap(bars)


CONFIGS = {
    "scoring": {
        "hybrid_scoring": {
            "buy_threshold": 70,
            "watch_threshold": 60,
            "no_action_threshold": 50,
            "do_not_buy_threshold": 35,
            "weights": {
                "trend_following": 18,
                "relative_strength": 20,
                "mean_reversion": 4,
                "breakout": 8,
                "volatility_risk": 12,
            },
        }
    }
}


def test_no_look_ahead():
    """Score at index t must not change when FUTURE bars are mutated."""
    replay = PriceOnlyReplay(CONFIGS, _FakeProvider(), window=22, horizon=20, step=5)
    closes = [{"date": f"2025-{(i // 27) + 1:02d}-{(i % 27) + 1:02d}", "close": 100.0 + i}
              for i in range(90)]
    idx = 70
    baseline = replay._score_at("TEST.NS", closes, idx, bench_change_pct=0.5)

    mutated = [dict(c) for c in closes]
    for j in range(idx + 1, len(mutated)):
        mutated[j]["close"] = 9999.0  # wildly change the future
    after = replay._score_at("TEST.NS", mutated, idx, bench_change_pct=0.5)

    assert baseline == after, f"look-ahead leak: {baseline} != {after}"
    print(f"[ok] no look-ahead: score at idx={idx} stable ({baseline}) despite mutated future")


def test_run_produces_episodes_and_bands():
    replay = PriceOnlyReplay(CONFIGS, _FakeProvider(n=120), window=22, horizon=20, step=5)
    symbols = [{"symbol": "AAA.NS"}, {"symbol": "BBB.NS"}, {"symbol": "CCC.NS"}]
    report = replay.run(symbols, lookback="2y")

    assert report["kind"] == "PRICE_ONLY_HISTORICAL_REPLAY"
    assert "DESCRIPTIVE ONLY" in report["disclaimer"]
    assert report["coverage"]["total_episodes"] > 0, "expected some episodes"
    for band in ("buy_grade", "watch_grade", "hold_grade", "low_grade"):
        assert band in report["by_score_band"]
        m = report["by_score_band"][band]
        assert 0.0 <= m["hit_rate_pct"] <= 100.0
    print(f"[ok] run(): scored={report['coverage']['symbols_scored']} "
          f"episodes={report['coverage']['total_episodes']} "
          f"edge={report['buy_grade_vs_rest_edge_pct']:+.2f}%")


def test_skips_insufficient_data():
    replay = PriceOnlyReplay(CONFIGS, _FakeProvider(n=10), window=22, horizon=20, step=5)
    report = replay.run([{"symbol": "AAA.NS"}], lookback="2y")
    assert report["coverage"]["symbols_scored"] == 0
    assert report["coverage"]["symbols_skipped_insufficient_data"] == 1
    print("[ok] insufficient-data symbols are skipped, not fabricated")


if __name__ == "__main__":
    test_no_look_ahead()
    test_run_produces_episodes_and_bands()
    test_skips_insufficient_data()
    print("\nALL PRICE-REPLAY TESTS PASSED")
