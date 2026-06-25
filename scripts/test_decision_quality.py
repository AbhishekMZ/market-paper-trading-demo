"""Offline, deterministic tests for the Decision Quality Engine.

Run:  python scripts/test_decision_quality.py

Simulates several runs with a known price path and asserts the measurement is
correct: high-score/acted signals that go up show positive forward returns,
declined/falling ones show negative; threshold + attribution + benchmark
comparison line up; readiness stays NOT_ENOUGH_DATA on a tiny sample (and never
enables live trading).
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import storage  # noqa: E402
from utils import write_json  # noqa: E402
from evaluation.forward_return_tracker import ForwardReturnTracker  # noqa: E402
from evaluation.benchmark_comparator import BenchmarkComparator  # noqa: E402
from evaluation import shadow_tracker, strategy_attribution, threshold_analysis  # noqa: E402
from evaluation import DecisionQualityEngine  # noqa: E402


def _reset_ledgers():
    write_json(storage.state_file("forward_returns.json"), {"open": {}, "archived": []})
    write_json(storage.state_file("benchmark_history.json"), [])


def _sig(symbol, score, price, acted, contributors=("trend_following",)):
    return {
        "symbol": symbol, "name": symbol, "signal_id": f"s-{symbol}", "label": "BUY_SMALL_PAPER" if acted else "WATCH",
        "score": score, "checkpoint": "close", "last_price": price, "led_to_paper_trade": acted,
        "news_risk_level": "NONE", "news_blocks_buy": False, "data_quality_verdict": "OK",
        "strategy_results": [{"strategy_name": c, "contributes_to_score": True} for c in contributors],
    }


def main() -> int:
    cfg = storage.load_config("evaluation.yml").get("evaluation", {})
    _reset_ledgers()

    # ITC rises (acted), SBIN falls (declined). 3 priced runs.
    paths = [
        ({"ITC.NS": 100.0, "SBIN.NS": 200.0}),
        ({"ITC.NS": 105.0, "SBIN.NS": 190.0}),
        ({"ITC.NS": 110.0, "SBIN.NS": 180.0}),
    ]
    tracker = ForwardReturnTracker(cfg)
    for prices in paths:
        sigs = [_sig("ITC.NS", 85, prices["ITC.NS"], acted=True),
                _sig("SBIN.NS", 40, prices["SBIN.NS"], acted=False, contributors=("mean_reversion",))]
        tracker.update(sigs, prices)
    tracker.save()
    eps = tracker.episodes()
    summ = tracker.summary()
    print("acted avg:", summ["acted"]["avg_return_pct"], "not_acted avg:", summ["not_acted"]["avg_return_pct"])
    assert summ["acted"]["avg_return_pct"] > 0, "acted (ITC rising) should be positive"
    assert summ["not_acted"]["avg_return_pct"] < 0, "declined (SBIN falling) should be negative"

    # Threshold analysis: ITC (85) is the only would-buy at T=80 and it rose.
    th = threshold_analysis.analyze(eps, cfg)
    row80 = next(r for r in th["table"] if r["threshold"] == 80)
    print("threshold 80:", row80)
    assert row80["would_buy_count"] == 1 and row80["avg_forward_return_pct"] > 0
    assert th["auto_tuning"] == "DISABLED"

    # Attribution: trend_following (ITC) should beat mean_reversion (SBIN).
    attr = strategy_attribution.analyze(eps)
    board = {r["strategy"]: r for r in attr["leaderboard"]}
    print("attribution:", {k: v["avg_forward_return_pct"] for k, v in board.items()})
    assert board["trend_following"]["avg_forward_return_pct"] > board["mean_reversion"]["avg_forward_return_pct"]

    # Shadow: acted picks outperformed declined candidates.
    sh = shadow_tracker.analyze(eps, cfg)
    assert sh["acted_vs_shadow_edge_pct"] > 0, "acted should beat shadow here"

    # Benchmark: portfolio +15% vs NIFTY +10% -> AHEAD.
    _reset_ledgers()
    bench = BenchmarkComparator(cfg)
    bench.update({"NIFTY 50": {"price": 100.0, "ok": True}}, portfolio_total=10000.0, starting_capital=10000.0)
    bench.update({"NIFTY 50": {"price": 110.0, "ok": True}}, portfolio_total=11500.0, starting_capital=10000.0)
    bench.save()
    comp = bench.comparison()
    print("benchmark:", comp["portfolio_return_pct"], "vs", comp["benchmark_return_pct"], "->", comp["verdict"])
    assert comp["ready"] and comp["verdict"] == "AHEAD" and comp["outperformance_pct"] == 5.0

    # Full engine end-to-end: structure + readiness on a tiny sample.
    _reset_ledgers()
    eng = DecisionQualityEngine(cfg)
    payload = eng.evaluate(
        signals=[_sig("ITC.NS", 85, 110.0, acted=True)],
        prices={"ITC.NS": 110.0},
        benchmarks={"NIFTY 50": {"price": 110.0, "ok": True}},
        portfolio_summary={"total_value": 10100.0, "starting_capital": 10000.0},
        checkpoint="close",
    )
    print("readiness:", payload["readiness"]["verdict"], "live:", payload["readiness"]["live_trading"])
    assert payload["readiness"]["verdict"] == "NOT_ENOUGH_DATA"
    assert payload["readiness"]["live_trading"] == "DISABLED"
    for key in ("metrics", "evidence_summary", "forward_returns", "shadow", "benchmark", "attribution", "threshold_analysis"):
        assert key in payload, f"missing {key}"
    evidence = payload["evidence_summary"]
    assert evidence["live_trading"] == "DISABLED"
    assert evidence["auto_tuning"] == "DISABLED"
    assert evidence["maturity_checks"], "evidence maturity checks should be present"

    _reset_ledgers()  # leave clean; the demo seed regenerates committed state
    print("OK: all decision-quality invariants hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
