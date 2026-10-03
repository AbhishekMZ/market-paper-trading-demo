"""Relevance scoring — does this article actually concern THIS company?

yfinance headlines arrive already tagged to a ticker, so the engine may keep
them unfiltered. GDELT is keyword-broad. Matching is phrase- and word-based:

* A configured alias or the company-name phrase (legal suffixes stripped) is a
  full hit.
* Shared group names (tata, adani, hdfc, …) do not count as a hit on their own,
  so a Tata group story does not attach to every Tata listing.
* Tokens match whole words, not substrings (`itc` does not match inside another
  word; `lt` is too short to use).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_LEGAL = {
    "ltd", "limited", "co", "corp", "corporation", "inc", "plc", "company",
}
_STOP = _LEGAL | {
    "the", "and", "of", "india", "indian", "&",
    "bank", "industries", "industry", "services", "state",
}
# First names shared by several listed companies. A hit on these alone is not
# evidence the article is about one subsidiary.
_GROUP = {
    "tata", "adani", "bajaj", "birla", "mahindra", "godrej", "hdfc", "icici",
}

_WORD_RE = re.compile(r"[a-z0-9]+")


def _words(text: Optional[str]) -> List[str]:
    return _WORD_RE.findall((text or "").lower())


def _symbol_root(symbol: str) -> str:
    return re.split(r"[.\-]", symbol or "")[0].strip().lower()


def _relevance_block(cfg: Any) -> Dict[str, Any]:
    if not isinstance(cfg, dict):
        return {}
    if isinstance(cfg.get("news"), dict):
        cfg = cfg["news"]
    block = cfg.get("relevance")
    if isinstance(block, dict):
        return block
    # Already the relevance mapping (aliases / group_name_rejects at the top).
    if "aliases" in cfg or "group_name_rejects" in cfg or "source_trust" in cfg:
        return cfg
    return {}


def group_rejects(cfg: Any = None) -> set:
    extra = _relevance_block(cfg).get("group_name_rejects")
    if isinstance(extra, list) and extra:
        return {str(x).lower() for x in extra}
    return set(_GROUP)


def company_tokens(symbol: str, company_name: Optional[str] = None, cfg: Any = None) -> List[str]:
    """Distinctive whole-word tokens. Group names and legal/sector fillers are omitted."""
    rejects = group_rejects(cfg)
    tokens = set()
    root = _symbol_root(symbol)
    if len(root) >= 3 and root not in rejects and root not in _STOP:
        tokens.add(root)
    for tok in _words(company_name):
        if len(tok) >= 3 and tok not in _STOP and tok not in rejects:
            tokens.add(tok)
    return sorted(tokens)


def _phrases(symbol: str, company_name: Optional[str], cfg: Any) -> List[str]:
    phrases: List[str] = []
    name_words = [w for w in _words(company_name) if w not in _LEGAL]
    if name_words:
        phrases.append(" ".join(name_words))
    aliases = _relevance_block(cfg).get("aliases") or {}
    if isinstance(aliases, dict):
        for key in (symbol, _symbol_root(symbol)):
            for alias in aliases.get(key) or []:
                text = str(alias).strip().lower()
                if text:
                    phrases.append(text)
    return phrases


def relevance_score(title: str, symbol: str, company_name: Optional[str] = None, cfg: Any = None) -> float:
    """0..1. Phrase/alias match is 1. Otherwise the share of distinctive tokens present as whole words."""
    text = (title or "").lower()
    if not text.strip():
        return 0.0
    for phrase in _phrases(symbol, company_name, cfg):
        if phrase and phrase in text:
            return 1.0
    toks = company_tokens(symbol, company_name, cfg)
    if not toks:
        return 0.0
    words = set(_words(text))
    hits = sum(1 for t in toks if t in words)
    if hits == 0:
        return 0.0
    return min(1.0, 0.5 + 0.5 * (hits / len(toks)))


def source_trust(source: Optional[str], cfg: Any = None) -> float:
    """Multiplier for a known desk. Unknown sources stay at 1.0 (no penalty, no boost)."""
    table = _relevance_block(cfg).get("source_trust") or {}
    if not isinstance(table, dict):
        return 1.0
    domain = (source or "").lower()
    best = 1.0
    for key, weight in table.items():
        if str(key).lower() in domain:
            try:
                best = max(best, float(weight))
            except (TypeError, ValueError):
                continue
    return best
