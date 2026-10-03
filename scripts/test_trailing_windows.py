"""Trailing-window and news-matching checks. No network.

Run:  python scripts/test_trailing_windows.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import storage  # noqa: E402
from context.features import excess_return_pct, scoring_view, trailing_return_pct  # noqa: E402
from news.event_classifier import classify_events  # noqa: E402
from news.news_risk_engine import stamp_for_archive  # noqa: E402
from news.relevance import relevance_score  # noqa: E402
from strategy.market_regime import DATA_INSUFFICIENT, NEUTRAL, RISK_OFF, RISK_ON, MarketRegimeEngine  # noqa: E402
from strategy.relative_strength import RelativeStrengthStrategy  # noqa: E402
from strategy.trend_following import TrendFollowingStrategy  # noqa: E402
from strategy.volatility_risk import VolatilityRiskStrategy  # noqa: E402


def test_weights_frozen():
    weights = storage.load_config("scoring.yml")["hybrid_scoring"]["weights"]
    assert weights["trend_following"] == 18
    assert weights["relative_strength"] == 20
    assert weights["market_regime"] == 16
    assert weights["volatility_risk"] == 12
    assert weights["news_event_risk"] == 14
    assert weights["portfolio_fit"] == 8
    assert weights["mean_reversion"] == 4
    assert weights["breakout"] == 8


def test_return_math():
    closes = [100.0, 110.0, 121.0]
    assert trailing_return_pct(closes, 1) == 10.0
    assert abs(trailing_return_pct(closes, 2) - 21.0) < 1e-6
    stock = [100.0] * 61 + [110.0]
    # 61 flat then a jump is not a clean 60-step path; build an explicit series.
    stock = [100.0]
    bench = [100.0]
    for _ in range(60):
        stock.append(stock[-1] * 1.002)
        bench.append(bench[-1] * 1.0)
    excess = excess_return_pct(stock, bench, 60)
    assert excess is not None and excess > 5.0


def test_relevance_and_events():
    cfg = storage.load_config("news.yml")
    assert relevance_score("Tata Motors bags a new order", "TATAMOTORS.NS", "Tata Motors", cfg) == 1.0
    assert relevance_score("Tata Motors bags a new order", "TATASTEEL.NS", "Tata Steel", cfg) == 0.0
    assert relevance_score("Tata group pledges support", "TATAMOTORS.NS", "Tata Motors", cfg) == 0.0
    assert relevance_score("default result published", "LT.NS", "Larsen & Toubro", cfg) == 0.0
    types, risk, _matched = classify_events(
        "Promoter pledge invocation on pledged shares", cfg.get("news") or cfg,
    )
    assert "PLEDGE" in types and risk.value == "HIGH"
    rows = stamp_for_archive(
        [{"title": "Tata Motors bags a new order", "symbol": "TATAMOTORS.NS"}],
        "close",
        "2026-10-03T16:00:00+05:30",
    )
    assert rows[0]["checkpoint"] == "close" and rows[0]["decision_at"].startswith("2026-10-03")


def test_strategies_use_trailing_features():
    up = scoring_view([{"close": 100.0 + i} for i in range(80)])
    ctx = {"hist_features": up}
    trend = TrendFollowingStrategy().evaluate("X.NS", {}, {}, ctx)
    assert trend.is_valid and trend.score_contribution > 60

    missing = RelativeStrengthStrategy().evaluate("X.NS", {"change_pct": 5.0}, {}, {})
    assert missing.is_valid is False

    calm = dict(up)
    calm["vol_percentile"] = 10.0
    calm["coverage"] = "ok"
    vol = VolatilityRiskStrategy().evaluate("X.NS", {}, {}, {"hist_features": calm})
    assert vol.is_valid and vol.score_contribution >= 80


def test_regime_uses_20_session_return():
    eng = MarketRegimeEngine()
    flat_day = {"NIFTY": {"ok": True, "change_pct": 0.2}}
    risk_on = eng.classify(flat_day, trailing={"return_20d_pct": 6.0})
    assert risk_on.regime == RISK_ON and risk_on.event_spike is False

    spike = eng.classify({"NIFTY": {"ok": True, "change_pct": 3.0}}, trailing={"return_20d_pct": 1.0})
    assert spike.regime == NEUTRAL and spike.event_spike is True and spike.score == 55.0

    risk_off = eng.classify(flat_day, trailing={"return_20d_pct": -6.0})
    assert risk_off.regime == RISK_OFF and risk_off.blocks_new_buys is True

    # A one-day pop without a 20-session read does not become RISK_ON.
    day_only = eng.classify({"NIFTY": {"ok": True, "change_pct": 1.2}})
    assert day_only.regime == NEUTRAL and day_only.blocks_new_buys is False

    assert eng.classify({}).regime == DATA_INSUFFICIENT

    from order_models import DataQuality, SignalLabel
    from strategy.hybrid_signal_engine import HybridSignalEngine

    hybrid = HybridSignalEngine({
        "scoring": {"hybrid_scoring": {"weights": {}}, "scoring": {"risk_penalties": {}}},
        "settings": {"data_quality": {}},
    })
    label, notes = hybrid._apply_gating(SignalLabel.BUY_SMALL_PAPER, spike, [], 0.8, DataQuality.GOOD)
    assert label == SignalLabel.MANUAL_REVIEW
    assert any("One-day index spike" in n for n in notes)
    assert spike.score == 55.0


def main() -> int:
    test_weights_frozen()
    test_return_math()
    test_relevance_and_events()
    test_strategies_use_trailing_features()
    test_regime_uses_20_session_return()
    print("OK: trailing windows, relevance, regime")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
