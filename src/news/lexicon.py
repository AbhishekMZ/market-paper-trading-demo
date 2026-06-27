"""Severity-weighted sentiment lexicon + negators.

Pure data + a loader. Defaults live in code so the scorer works with no config;
config tiers under news.yml -> sentiment.weighted_terms override/extend them.
Negative magnitudes intentionally exceed positive ceilings (caution-first).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

_DEFAULT_TIERS = {
    "critical_negative": (-1.0, ["fraud", "scam", "ponzi", "embezzle", "siphon", "forensic audit"]),
    "strong_negative": (-0.7, ["probe", "investigation", "default", "lawsuit", "downgrade", "insolvency", "bankruptcy"]),
    "mild_negative": (-0.4, ["miss", "weak results", "profit warning", "recall", "fine", "penalty"]),
    "mild_positive": (0.4, ["order win", "upgrade", "expansion", "new contract", "wins order"]),
    "strong_positive": (0.6, ["strong results", "record profit", "debt reduction", "beats"]),
}
_DEFAULT_NEGATORS = [
    "denies", "denied", "deny", "no", "not", "cleared of", "rejects", "rejected",
    "dismisses", "dismissed", "refutes", "unfounded", "false", "without merit",
]


@dataclass
class WeightedLexicon:
    terms: Dict[str, float] = field(default_factory=dict)
    negators: List[str] = field(default_factory=list)


def _sentiment_block(cfg: Any) -> Dict[str, Any]:
    if isinstance(cfg, dict):
        return cfg.get("sentiment") or {}
    return {}


def load_lexicon(cfg: Any = None) -> WeightedLexicon:
    """Build the lexicon: code defaults, then config tier + legacy overrides."""
    terms: Dict[str, float] = {}
    for _, (weight, words) in _DEFAULT_TIERS.items():
        for t in words:
            terms[t] = weight

    s = _sentiment_block(cfg)
    wt = s.get("weighted_terms")
    if isinstance(wt, dict):
        for _, spec in wt.items():
            if not isinstance(spec, dict):
                continue
            w = float(spec.get("weight", 0.0))
            for t in spec.get("terms", []) or []:
                terms[str(t).lower()] = w

    # Legacy flat lists are a fallback — only fill terms not already weighted.
    for t in s.get("negative_keywords", []) or []:
        terms.setdefault(str(t).lower(), -0.6)
    for t in s.get("positive_keywords", []) or []:
        terms.setdefault(str(t).lower(), 0.4)

    negators = [str(n).lower() for n in (s.get("negators") or _DEFAULT_NEGATORS)]
    return WeightedLexicon(terms=terms, negators=negators)
