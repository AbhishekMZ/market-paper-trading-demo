"""Offline, deterministic tests for the news risk overlay.

Run:  python scripts/test_news_risk_engine.py

No network: GDELT is stubbed and news items are supplied inline. Asserts the
cardinal invariants:
  * HIGH/CRITICAL adverse news BLOCKS a paper buy (downgrades the label).
  * Positive news never creates/upgrades a buy and never changes the score.
  * No news -> neutral no-op.
  * CRITICAL news on a HELD position -> EXIT_REVIEW (advisory).
  * A CRITICAL assessment produces an email alert payload.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import storage  # noqa: E402
import news.providers as news_providers  # noqa: E402
from news import NewsRiskEngine  # noqa: E402
from order_models import DataQuality, RiskLevel, SignalLabel, TradeSignal  # noqa: E402

# Keep it fully offline.
news_providers.GDELTNewsProvider._query = lambda self, query_name: []


def _engine() -> NewsRiskEngine:
    cfg = storage.load_config("news.yml").get("news", {})
    cfg.setdefault("providers", {}).setdefault("gdelt", {})["enabled"] = False
    return NewsRiskEngine(cfg)


def _sig(symbol="ABC.NS", name="ABC Ltd", label=SignalLabel.BUY_SMALL_PAPER, score=85.0) -> TradeSignal:
    return TradeSignal(signal_id="t", symbol=symbol, name=name, exchange="NSE", score=score,
                       label=label, risk_level=RiskLevel.LOW, confidence=0.7,
                       data_quality=DataQuality.GOOD, reason="strong trend")


def _news(title):
    return [{"title": title, "publisher": "TEST", "provider_publish_time": None}]


def main() -> int:
    eng = _engine()

    # 1) CRITICAL adverse news -> block buy.
    a = eng.assess("ABC.NS", "ABC Ltd", prefetched_news=_news("ABC hit by SEBI fraud probe; forensic audit"), held=False)
    s = _sig()
    eng.apply_to_signal(s, a)
    assert a.news_risk_level.value == "CRITICAL" and a.blocks_buy, "CRITICAL must block"
    assert s.label == SignalLabel.NO_ACTION and s.news_blocks_buy, "buy must be blocked -> NO_ACTION"

    # 2) Positive news -> no block, label + score unchanged.
    a2 = eng.assess("ABC.NS", "ABC Ltd", prefetched_news=_news("ABC wins order; strong results, record profit"), held=False)
    s2 = _sig()
    eng.apply_to_signal(s2, a2)
    assert not a2.blocks_buy and s2.label == SignalLabel.BUY_SMALL_PAPER, "positive news must not block"
    assert s2.score == 85.0, "overlay must never change the score"

    # 3) No news -> neutral no-op.
    a3 = eng.assess("ABC.NS", "ABC Ltd", prefetched_news=[], held=False)
    s3 = _sig()
    eng.apply_to_signal(s3, a3)
    assert not a3.news_available and s3.label == SignalLabel.BUY_SMALL_PAPER

    # 4) CRITICAL on a held position -> EXIT_REVIEW.
    a4 = eng.assess("ABC.NS", "ABC Ltd", prefetched_news=_news("ABC fraud probe widens"), held=True)
    s4 = _sig(label=SignalLabel.HOLD)
    eng.apply_to_signal(s4, a4)
    assert a4.exit_review_for_holding and s4.label == SignalLabel.EXIT_REVIEW

    # 5) Alert payload for CRITICAL.
    alert = eng.build_alert(a, was_buy_candidate=True, held=False)
    assert alert and "CRITICAL" in alert["subject"]

    # 6) New: assessment carries finance-aware sentiment fields.
    assert a.sentiment_score < 0, "CRITICAL fraud news must read negative"
    assert 0.0 <= a.sentiment_confidence <= 1.0
    assert a2.sentiment_score > 0, "order-win/strong-results must read positive"
    # Overlay never relaxes caution: positive news still does not block or change score.
    assert not a2.blocks_buy and s2.score == 85.0

    print("OK: all news risk engine invariants hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
