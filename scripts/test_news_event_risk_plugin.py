"""Offline tests for the news_event_risk scoring plugin.

The plugin scores the risk engine's enriched items. It does not read a second
headline list, and missing news does not contribute a neutral 65.

Run:  python scripts/test_news_event_risk_plugin.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import news.providers as news_providers  # noqa: E402
import storage  # noqa: E402
from news.news_risk_engine import NewsRiskEngine  # noqa: E402
from strategy.base import NEGATIVE, POSITIVE  # noqa: E402
from strategy.hybrid_signal_engine import HybridSignalEngine  # noqa: E402
from strategy.news_event_risk import NewsEventRiskStrategy  # noqa: E402

news_providers.GDELTNewsProvider._query = lambda self, query_name: []


def _engine() -> NewsRiskEngine:
    cfg = storage.load_config("news.yml").get("news", {})
    cfg.setdefault("providers", {}).setdefault("gdelt", {})["enabled"] = False
    return NewsRiskEngine(cfg)


def _cfg():
    return storage.load_config("news.yml").get("news", {})


def _items(*titles: str):
    raw = [{"title": t, "publisher": "TEST"} for t in titles]
    return _engine().collect_items("ABC.NS", "ABC Ltd", raw)


def _ctx(items):
    return {"news_cfg": _cfg(), "news_items": items}


def main() -> int:
    p = NewsEventRiskStrategy()

    none = p.evaluate("ABC.NS", {"headlines": ["fraud probe; forensic audit"]}, {}, _ctx([]))
    assert none.is_valid is False and none.contributes_to_score is False

    strong_neg = p.evaluate("ABC.NS", {}, {}, _ctx(_items("ABC hit by fraud probe; forensic audit")))
    assert strong_neg.is_valid and strong_neg.signal == NEGATIVE and strong_neg.score_contribution < 45

    strong_pos = p.evaluate(
        "ABC.NS", {}, {}, _ctx(_items("ABC strong results, record profit; debt reduction")),
    )
    assert strong_pos.is_valid and strong_pos.signal == POSITIVE and strong_pos.score_contribution > 68

    mild_neg = p.evaluate("ABC.NS", {}, {}, _ctx(_items("ABC Q3 profit misses estimates")))
    assert mild_neg.score_contribution > strong_neg.score_contribution
    assert mild_neg.score_contribution < 65

    # Cross-source agreement firms the read. Several titles from one provider do not
    # count as a second source — that matches NewsRiskEngine.aggregate.
    def _scored(pol, provider):
        return {"sentiment_score": pol, "sentiment_confidence": 0.8, "provider": provider,
                "relevance": 1.0, "age_hours": 2.0}

    one = p.evaluate("ABC.NS", {}, {}, _ctx([_scored(-0.9, "yfinance")]))
    agreed = p.evaluate("ABC.NS", {}, {}, _ctx([_scored(-0.9, "yfinance"), _scored(-0.9, "gdelt")]))
    assert one.signal == NEGATIVE and agreed.signal == NEGATIVE
    assert agreed.score_contribution <= one.score_contribution, (agreed.score_contribution, one.score_contribution)

    # Absence drops out of the blend instead of pulling it toward 65.
    hybrid = HybridSignalEngine({
        "scoring": {
            "hybrid_scoring": {
                "weights": {"news_event_risk": 14},
                "experimental_strategies": {},
            },
            "scoring": {"risk_penalties": {}},
        },
        "settings": {"data_quality": {}},
    })
    sig = hybrid.evaluate(
        "ABC.NS",
        {"ok": True, "price": 100.0, "change_pct": 0.0, "graph_points": 0},
        {},
        {"news_items": [], "news_cfg": _cfg()},
    )
    news_row = next(r for r in sig.strategy_results if r["strategy_name"] == "news_event_risk")
    assert news_row["is_valid"] is False and news_row["contributes_to_score"] is False

    print("OK: news_event_risk plugin sentiment scoring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
