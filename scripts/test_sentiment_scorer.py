"""Offline, deterministic tests for the finance-aware sentiment scorer.

Run:  python scripts/test_sentiment_scorer.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from news.lexicon import load_lexicon  # noqa: E402
from news.sentiment import SentimentScore, score_text  # noqa: E402
from news.base import NewsSentiment  # noqa: E402
from news.sentiment import recency_weight  # noqa: E402
from news.relevance import company_tokens  # noqa: E402


def test_lexicon_defaults_and_overrides():
    lex = load_lexicon()
    assert lex.terms["fraud"] == -1.0
    assert lex.terms["miss"] == -0.4
    assert lex.terms["strong results"] == 0.6
    assert "denies" in lex.negators
    # config tiers override/extend defaults; defaults still present.
    lex2 = load_lexicon({"sentiment": {"weighted_terms": {
        "x": {"weight": -0.5, "terms": ["foo bar"]}}}})
    assert lex2.terms["foo bar"] == -0.5
    assert lex2.terms["fraud"] == -1.0


def test_score_text_weighting_and_deadband():
    neg = score_text("Company hit by fraud probe")
    assert neg.label == NewsSentiment.NEGATIVE and neg.polarity < 0
    pos = score_text("Company posts strong results and record profit")
    assert pos.label == NewsSentiment.POSITIVE and pos.polarity > 0
    flat = score_text("The company held its annual general meeting today")
    assert flat.label == NewsSentiment.NEUTRAL and abs(flat.polarity) < 0.15
    # severity ordering: fraud is more bearish than a mild miss.
    assert score_text("fraud probe").polarity < score_text("earnings miss").polarity
    # positive ceiling stays below negative magnitude (caution-first).
    assert abs(pos.polarity) < abs(score_text("fraud scam probe").polarity)


def test_negation_neutralizes():
    s = score_text("Company denies fraud allegations")
    assert s.label == NewsSentiment.NEUTRAL and "fraud" in s.negated
    s2 = score_text("Company hit by fraud probe")
    assert s2.label == NewsSentiment.NEGATIVE and not s2.negated


def test_recency_decay():
    fresh = recency_weight(1)
    mid = recency_weight(60)
    old = recency_weight(500)
    assert fresh == 1.0
    assert 0.3 <= mid < 1.0
    assert old == 0.3
    assert fresh > mid > old


def test_entity_proximity_confidence():
    toks = company_tokens("RELIANCE.NS", "Reliance Industries")
    near = score_text("Reliance hit by fraud probe", company_tokens=toks)
    far = score_text("Tata Steel fraud probe widens across the sector", company_tokens=toks)
    # same bearish terms; confidence higher when the company is named near them.
    assert near.confidence > far.confidence


def main() -> int:
    test_lexicon_defaults_and_overrides()
    test_score_text_weighting_and_deadband()
    test_negation_neutralizes()
    test_recency_decay()
    test_entity_proximity_confidence()
    print("OK: sentiment scorer tests pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
