"""Event classification — map headline text to event types + a risk level.

Driven by `news.yml -> event_rules` (text keywords -> event type + risk). The
worst risk across all matched rules wins, so one fraud keyword outranks several
benign ones. Deterministic and fully auditable (matched keywords are recorded).
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from news.base import NewsRiskLevel, coerce_risk, max_risk

# Built-in fallback if config is missing, so the engine never depends on YAML.
_DEFAULT_RULES = [
    {"type": "FRAUD", "risk": "CRITICAL", "keywords": ["fraud", "scam", "embezzle", "ponzi", "forensic audit"]},
    {"type": "REGULATORY", "risk": "HIGH", "keywords": ["sebi", "regulatory action", "probe", "investigation", "raid", "ban", "show cause", "sfio"]},
    {"type": "LEGAL", "risk": "HIGH", "keywords": ["lawsuit", "litigation", "insolvency", "bankruptcy", "default", "nclt", "arrest"]},
    {"type": "RATING_DOWNGRADE", "risk": "HIGH", "keywords": ["downgrade", "rating cut", "outlook negative", "credit concern"]},
    {"type": "MANAGEMENT_CHANGE", "risk": "MEDIUM", "keywords": ["resignation", "steps down", "resigns", "auditor resigns"]},
    {"type": "EARNINGS_MISS", "risk": "MEDIUM", "keywords": ["profit falls", "loss widens", "misses estimates", "weak results", "margin pressure", "profit warning"]},
    {"type": "EARNINGS_BEAT", "risk": "NONE", "keywords": ["beats estimates", "strong results", "profit rises", "record profit"]},
    {"type": "ORDER_WIN", "risk": "NONE", "keywords": ["order win", "wins contract", "bags order", "new order"]},
    {"type": "EXPANSION", "risk": "NONE", "keywords": ["expansion", "capacity addition", "new plant"]},
    {"type": "MACRO", "risk": "LOW", "keywords": ["rbi", "inflation", "rate hike", "crude oil", "fed", "gst"]},
]


def _rules(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    rules = (cfg or {}).get("event_rules")
    return rules if isinstance(rules, list) and rules else _DEFAULT_RULES


def classify_events(text: str, cfg: Dict[str, Any]) -> Tuple[List[str], NewsRiskLevel, List[str]]:
    """Return (event_types, worst_risk_level, matched_keywords) for one article."""
    low = (text or "").lower()
    types: List[str] = []
    matched: List[str] = []
    worst = NewsRiskLevel.NONE
    for rule in _rules(cfg):
        hits = [kw for kw in rule.get("keywords", []) if kw.lower() in low]
        if not hits:
            continue
        types.append(rule.get("type", "OTHER"))
        matched.extend(hits)
        worst = max_risk(worst, coerce_risk(rule.get("risk", "NONE")))
    return sorted(set(types)), worst, sorted(set(matched))
