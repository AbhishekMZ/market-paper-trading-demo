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


def main() -> int:
    test_lexicon_defaults_and_overrides()
    test_score_text_weighting_and_deadband()
    print("OK: sentiment scorer tests pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
