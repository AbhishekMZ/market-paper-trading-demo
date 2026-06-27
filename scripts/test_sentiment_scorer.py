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
from news.sentiment import AggregateSentiment, aggregate  # noqa: E402
from news.sentiment import classify_sentiment, aggregate_sentiment  # noqa: E402


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


def test_aggregate_agreement_and_conflict():
    # records: (polarity, confidence, provider, relevance, age_hours)
    agree = aggregate([(-0.8, 0.9, "yfinance", 1.0, 1.0), (-0.7, 0.8, "gdelt", 0.9, 2.0)])
    assert agree.label == NewsSentiment.NEGATIVE and agree.sources_agree and not agree.conflict
    assert agree.n_sources == 2 and agree.confidence > 0.7

    conflict = aggregate([(-0.8, 0.9, "yfinance", 1.0, 1.0), (0.7, 0.8, "gdelt", 1.0, 1.0)])
    assert conflict.conflict and conflict.confidence < 0.6

    single = aggregate([(-0.8, 0.9, "yfinance", 1.0, 1.0)])
    assert single.n_sources == 1 and single.confidence < 0.9 and single.label == NewsSentiment.NEGATIVE

    empty = aggregate([])
    assert empty.label == NewsSentiment.NEUTRAL and empty.n_sources == 0


def test_backcompat_wrappers():
    label, neg, pos = classify_sentiment("fraud probe", {})
    assert label == NewsSentiment.NEGATIVE
    assert "fraud" in neg and "probe" in neg and pos == []
    assert aggregate_sentiment([NewsSentiment.POSITIVE, NewsSentiment.NEGATIVE]) == NewsSentiment.NEGATIVE
    assert aggregate_sentiment([]) == NewsSentiment.NEUTRAL


def test_matching_robustness():
    # negators must not prefix-match ordinary words (Critical fix).
    assert score_text("North zone fraud probe").label == NewsSentiment.NEGATIVE
    assert score_text("November fraud probe results").label == NewsSentiment.NEGATIVE
    assert score_text("Company notes fraud probe ongoing").label == NewsSentiment.NEGATIVE
    # genuine negation still neutralizes.
    assert score_text("Company denies fraud").label == NewsSentiment.NEUTRAL
    # terms must not prefix-match unrelated words, but must catch inflections.
    assert score_text("Company unveils new mission statement").label == NewsSentiment.NEUTRAL
    assert score_text("The finer details were released").label == NewsSentiment.NEUTRAL
    assert score_text("Q3 profit misses estimates").label == NewsSentiment.NEGATIVE
    # an empty company token must not fabricate a proximity boost.
    assert score_text("fraud probe", company_tokens=[""]).confidence == score_text("fraud probe").confidence


def test_aggregate_handles_none_and_nan():
    r = aggregate([(-0.5, 0.8, "yfinance", None, None)])
    assert r.label == NewsSentiment.NEGATIVE and r.n_sources == 1
    r2 = aggregate([(float("nan"), 0.8, "yfinance", 1.0, 1.0)])
    assert r2.label == NewsSentiment.NEUTRAL  # NaN polarity -> neutral, no crash


def main() -> int:
    test_lexicon_defaults_and_overrides()
    test_score_text_weighting_and_deadband()
    test_negation_neutralizes()
    test_recency_decay()
    test_entity_proximity_confidence()
    test_aggregate_agreement_and_conflict()
    test_backcompat_wrappers()
    test_matching_robustness()
    test_aggregate_handles_none_and_nan()
    print("OK: sentiment scorer tests pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
