"""Keyword-based news sentiment (deterministic, explainable, no ML in v1).

Negative news is weighted more heavily than positive — the system must not be
talked into optimism by a cheerful headline. Output feeds the risk overlay, so
NEUTRAL is the safe default when signals are weak or absent.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from news.base import NewsSentiment

_DEFAULT_NEGATIVE = [
    "fraud", "scam", "probe", "investigation", "penalty", "downgrade", "weak results",
    "loss", "default", "resignation", "regulatory action", "lawsuit", "debt concern",
    "raid", "ban", "fine", "recall", "miss", "profit warning", "insolvency", "bankruptcy",
]
_DEFAULT_POSITIVE = [
    "strong results", "order win", "expansion", "approval", "upgrade",
    "margin improvement", "debt reduction", "record", "beats", "wins order", "new contract",
]


def _keywords(cfg: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    s = (cfg or {}).get("sentiment", {})
    neg = [k.lower() for k in s.get("negative_keywords", _DEFAULT_NEGATIVE)]
    pos = [k.lower() for k in s.get("positive_keywords", _DEFAULT_POSITIVE)]
    return neg, pos


def classify_sentiment(text: str, cfg: Dict[str, Any]) -> Tuple[NewsSentiment, List[str], List[str]]:
    """Return (sentiment, matched_negative, matched_positive) for one headline/summary."""
    low = (text or "").lower()
    neg_kw, pos_kw = _keywords(cfg)
    neg_hits = sorted({kw for kw in neg_kw if kw in low})
    pos_hits = sorted({kw for kw in pos_kw if kw in low})
    if neg_hits and len(neg_hits) >= len(pos_hits):
        sentiment = NewsSentiment.NEGATIVE
    elif pos_hits and not neg_hits:
        sentiment = NewsSentiment.POSITIVE
    elif neg_hits:
        sentiment = NewsSentiment.NEGATIVE  # tie with any negative -> stay cautious
    else:
        sentiment = NewsSentiment.NEUTRAL
    return sentiment, neg_hits, pos_hits


def aggregate_sentiment(sentiments: List[NewsSentiment]) -> NewsSentiment:
    """Combine per-item sentiments. Any negative dominates positives (caution-first)."""
    if not sentiments:
        return NewsSentiment.NEUTRAL
    neg = sum(1 for s in sentiments if s == NewsSentiment.NEGATIVE)
    pos = sum(1 for s in sentiments if s == NewsSentiment.POSITIVE)
    if neg:
        return NewsSentiment.NEGATIVE
    if pos:
        return NewsSentiment.POSITIVE
    return NewsSentiment.NEUTRAL
