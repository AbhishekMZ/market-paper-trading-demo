"""Offline, deterministic tests for the finance-aware sentiment scorer.

Run:  python scripts/test_sentiment_scorer.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from news.lexicon import load_lexicon  # noqa: E402


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


def main() -> int:
    test_lexicon_defaults_and_overrides()
    print("OK: sentiment scorer tests pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
