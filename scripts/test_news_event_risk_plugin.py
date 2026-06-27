"""Offline tests for the news_event_risk scoring plugin (shared sentiment scorer).

Run:  python scripts/test_news_event_risk_plugin.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import storage  # noqa: E402
from strategy.news_event_risk import NewsEventRiskStrategy  # noqa: E402
from strategy.base import NEGATIVE, NEUTRAL, POSITIVE  # noqa: E402


def _ctx():
    return {"news_cfg": storage.load_config("news.yml").get("news", {})}


def _md(headlines):
    return {"headlines": headlines}


def main() -> int:
    p = NewsEventRiskStrategy()
    ctx = _ctx()

    none = p.evaluate("X", _md([]), {}, ctx)
    assert none.score_contribution == 65.0 and none.signal == NEUTRAL

    strong_neg = p.evaluate("X", _md(["Company hit by fraud probe; forensic audit"]), {}, ctx)
    assert strong_neg.signal == NEGATIVE and strong_neg.score_contribution < 45

    strong_pos = p.evaluate("X", _md(["Strong results, record profit; debt reduction"]), {}, ctx)
    assert strong_pos.signal == POSITIVE and strong_pos.score_contribution > 68

    # A single mild negative is damped by low confidence — not slammed.
    mild_neg = p.evaluate("X", _md(["Q3 profit misses estimates"]), {}, ctx)
    assert mild_neg.score_contribution > strong_neg.score_contribution
    assert mild_neg.score_contribution < 65

    # Corroboration must FIRM the score: more agreeing negative headlines ->
    # a score at least as low as a single one (not softer). Regression for the
    # single-provider dilution bug.
    one = p.evaluate("X", _md(["fraud probe; forensic audit"]), {}, ctx)
    many = p.evaluate("X", _md(["fraud probe", "forensic audit fraud", "SEBI investigation launched"]), {}, ctx)
    assert many.signal == NEGATIVE
    assert many.score_contribution <= one.score_contribution, (many.score_contribution, one.score_contribution)

    print("OK: news_event_risk plugin sentiment scoring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
