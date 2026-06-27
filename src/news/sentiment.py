"""Finance-aware news sentiment scorer (deterministic, explainable, no ML).

`score_text` turns one headline/summary into a SentimentScore: a signed polarity
in [-1, +1], a label, and a confidence in [0, 1], plus the terms that drove it.
`aggregate` combines per-article scores, raising confidence on cross-source
agreement and cutting it on single-source / conflicting reads. Negative news is
weighted more heavily than positive — the system is never talked into optimism.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from news.base import NewsSentiment
from news.lexicon import load_lexicon

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _sent_cfg(cfg: Any) -> Dict[str, Any]:
    if isinstance(cfg, dict):
        return cfg.get("sentiment") or {}
    return {}


def _label_for(polarity: float, deadband: float) -> NewsSentiment:
    if abs(polarity) < deadband:
        return NewsSentiment.NEUTRAL
    return NewsSentiment.POSITIVE if polarity > 0 else NewsSentiment.NEGATIVE


@dataclass
class SentimentScore:
    polarity: float = 0.0
    label: NewsSentiment = NewsSentiment.NEUTRAL
    confidence: float = 0.0
    matched: List[Tuple[str, float]] = field(default_factory=list)
    negated: List[str] = field(default_factory=list)
    reason: str = ""


def score_text(text: str, cfg: Any = None, *, relevance: float = 1.0,
               age_hours: Optional[float] = None,
               company_tokens: Optional[List[str]] = None) -> SentimentScore:
    low = (text or "").lower()
    if not low.strip():
        return SentimentScore(reason="empty text -> neutral")
    lex = load_lexicon(cfg)
    deadband = float(_sent_cfg(cfg).get("neutral_deadband", 0.15))

    surviving: List[Tuple[str, float]] = []
    for term, w in lex.terms.items():
        if re.search(r"\b" + re.escape(term), low):
            surviving.append((term, w))

    total = sum(w for _, w in surviving)
    polarity = math.tanh(total)
    label = _label_for(polarity, deadband)

    strength = sum(abs(w) for _, w in surviving)
    conf = _clamp(min(1.0, strength / 1.5) * float(relevance), 0.0, 1.0)
    if not surviving:
        conf = min(conf, 0.1)

    reason = f"matched={surviving}; polarity={polarity:.2f}, confidence={conf:.2f}"
    return SentimentScore(round(polarity, 3), label, round(conf, 3),
                          list(surviving), [], reason)


# ---------------------------------------------------------------------------
# Legacy back-compat wrappers (preserved so news_risk_engine.py keeps working)
# ---------------------------------------------------------------------------

def classify_sentiment(text: str, cfg: Any) -> Tuple[NewsSentiment, List[str], List[str]]:
    """Legacy shape: (label, matched_negative, matched_positive). Delegates to score_text."""
    sc = score_text(text, cfg)
    neg = sorted(t for t, w in sc.matched if w < 0)
    pos = sorted(t for t, w in sc.matched if w > 0)
    return sc.label, neg, pos


def aggregate_sentiment(sentiments: List[NewsSentiment]) -> NewsSentiment:
    """Legacy label-only combine: any negative dominates (caution-first)."""
    if not sentiments:
        return NewsSentiment.NEUTRAL
    if any(s == NewsSentiment.NEGATIVE for s in sentiments):
        return NewsSentiment.NEGATIVE
    if any(s == NewsSentiment.POSITIVE for s in sentiments):
        return NewsSentiment.POSITIVE
    return NewsSentiment.NEUTRAL
