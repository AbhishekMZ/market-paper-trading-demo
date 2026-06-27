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


def recency_weight(age_hours: Optional[float], cfg: Any = None) -> float:
    """1.0 for fresh items, decaying linearly to floor_weight by max_age_hours."""
    if age_hours is None:
        return 1.0
    s = _sent_cfg(cfg).get("recency", {})
    full = float(s.get("full_weight_hours", 24))
    floor = float(s.get("floor_weight", 0.3))
    fr = cfg.get("freshness", {}) if isinstance(cfg, dict) else {}
    max_age = float(fr.get("max_age_hours", 96))
    if age_hours <= full or max_age <= full:
        return 1.0 if age_hours <= full else floor
    if age_hours >= max_age:
        return floor
    frac = (age_hours - full) / (max_age - full)
    return 1.0 - frac * (1.0 - floor)


def score_text(text: str, cfg: Any = None, *, relevance: float = 1.0,
               age_hours: Optional[float] = None,
               company_tokens: Optional[List[str]] = None) -> SentimentScore:
    low = (text or "").lower()
    if not low.strip():
        return SentimentScore(reason="empty text -> neutral")
    lex = load_lexicon(cfg)
    sent = _sent_cfg(cfg)
    deadband = float(sent.get("neutral_deadband", 0.15))
    window = int(sent.get("negation_window", 4))

    tokens = [(m.group(0), m.start()) for m in _TOKEN_RE.finditer(low)]
    token_starts = [s for _, s in tokens]

    def tok_index(char_pos: int) -> int:
        idx = 0
        for i, s in enumerate(token_starts):
            if s <= char_pos:
                idx = i
            else:
                break
        return idx

    surviving: List[Tuple[str, float, int]] = []
    negated: List[str] = []
    for term, w in lex.terms.items():
        m = re.search(r"\b" + re.escape(term), low)
        if not m:
            continue
        start = m.start()
        lo = max(0, tok_index(start) - window)
        win_text = low[token_starts[lo]:start] if token_starts else ""
        if any(re.search(r"\b" + re.escape(n), win_text) for n in lex.negators):
            negated.append(term)
            continue
        surviving.append((term, w, start))

    total = sum(w for _, w, _ in surviving)
    polarity = math.tanh(total)
    label = _label_for(polarity, deadband)

    strength = sum(abs(w) for _, w, _ in surviving)
    base = min(1.0, strength / 1.5)

    prox_factor = 1.0
    if company_tokens:
        ep = sent.get("entity_proximity", {})
        near_boost = float(ep.get("near_boost", 0.2))
        far_pen = float(ep.get("far_penalty", 0.3))
        pwin = int(ep.get("window_tokens", 6))
        comp_idx = [tok_index(mm.start()) for mm in
                    (re.search(r"\b" + re.escape(ct), low) for ct in company_tokens) if mm]
        if not comp_idx:
            prox_factor = 1.0 - far_pen
        elif surviving:
            term_idx = [tok_index(s) for _, _, s in surviving]
            nearest = min(abs(a - b) for a in term_idx for b in comp_idx)
            prox_factor = (1.0 + near_boost) if nearest <= pwin else (1.0 - far_pen)

    rec = recency_weight(age_hours, cfg)
    conf = _clamp(base * float(relevance) * rec * prox_factor, 0.0, 1.0)
    if not surviving:
        conf = min(conf, 0.1)

    matched = [(t, w) for t, w, _ in surviving]
    reason = (f"matched={matched}" + (f"; negated={negated}" if negated else "")
              + f"; polarity={polarity:.2f}, confidence={conf:.2f}")
    return SentimentScore(round(polarity, 3), label, round(conf, 3), matched, negated, reason)


@dataclass
class AggregateSentiment:
    label: NewsSentiment = NewsSentiment.NEUTRAL
    polarity: float = 0.0
    confidence: float = 0.0
    sources_agree: bool = False
    conflict: bool = False
    n_sources: int = 0
    reason: str = ""


def aggregate(records: List[Tuple[float, float, str, float, Optional[float]]],
              cfg: Any = None) -> AggregateSentiment:
    """Combine per-article (polarity, confidence, provider, relevance, age_hours).

    Confidence rises when ≥2 distinct sources agree, falls on single-source or
    when sources conflict. Polarity is a relevance×recency-weighted mean.
    """
    sent = _sent_cfg(cfg)
    deadband = float(sent.get("neutral_deadband", 0.15))
    cc = sent.get("confidence", {})
    single_pen = float(cc.get("single_source_penalty", 0.3))
    conflict_pen = float(cc.get("conflict_penalty", 0.5))
    agree_bonus = float(cc.get("agreement_bonus", 0.25))

    if not records:
        return AggregateSentiment(confidence=0.1, reason="no items -> neutral")

    weights = [max(0.0, float(rel)) * recency_weight(age, cfg)
               for (_pol, _conf, _prov, rel, age) in records]
    tw = sum(weights)
    if tw > 0:
        pol_mean = sum(w * r[0] for r, w in zip(records, weights)) / tw
        conf_mean = sum(w * r[1] for r, w in zip(records, weights)) / tw
    else:
        pol_mean = sum(r[0] for r in records) / len(records)
        conf_mean = sum(r[1] for r in records) / len(records)

    by_source: Dict[str, float] = {}
    for pol, _conf, prov, _rel, _age in records:
        by_source[prov] = by_source.get(prov, 0.0) + pol
    signs = {p: (-1 if s < -deadband else 1 if s > deadband else 0) for p, s in by_source.items()}
    non_neutral = [v for v in signs.values() if v != 0]
    n_sources = len(by_source)
    sources_agree = len(non_neutral) >= 2 and len(set(non_neutral)) == 1
    conflict = (1 in non_neutral) and (-1 in non_neutral)

    conf = conf_mean
    if conflict:
        conf *= (1.0 - conflict_pen)
    elif sources_agree:
        conf = min(1.0, conf * (1.0 + agree_bonus))
    elif n_sources < 2:
        conf *= (1.0 - single_pen)

    label = _label_for(pol_mean, deadband)
    reason = (f"{len(records)} item(s)/{n_sources} source(s); polarity {pol_mean:.2f}, "
              f"confidence {conf:.2f}"
              + ("; sources agree" if sources_agree else "")
              + ("; sources conflict" if conflict else ""))
    return AggregateSentiment(label, round(pol_mean, 3), round(_clamp(conf, 0.0, 1.0), 3),
                              sources_agree, conflict, n_sources, reason)


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
