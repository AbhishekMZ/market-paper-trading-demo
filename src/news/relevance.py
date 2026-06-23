"""Relevance scoring — does this article actually concern THIS company?

yfinance headlines arrive already tagged to a ticker, so they're trusted. GDELT
is keyword-broad and can surface loosely-related stories, so we insist on a
symbol/company-name token match before letting it influence a decision.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_STOP = {
    "ltd", "limited", "the", "and", "co", "corporation", "corp", "inc", "plc",
    "india", "indian", "company", "industries", "enterprises", "&",
}


def _symbol_root(symbol: str) -> str:
    # "RELIANCE.NS" -> "reliance"
    return re.split(r"[.\-]", symbol or "")[0].strip().lower()


def company_tokens(symbol: str, company_name: Optional[str]) -> List[str]:
    tokens = set()
    root = _symbol_root(symbol)
    if root:
        tokens.add(root)
    for tok in re.split(r"[^a-z0-9]+", (company_name or "").lower()):
        if len(tok) >= 3 and tok not in _STOP:
            tokens.add(tok)
    return sorted(tokens)


def relevance_score(title: str, symbol: str, company_name: Optional[str]) -> float:
    """0..1 — fraction of company tokens that appear in the title/summary text."""
    toks = company_tokens(symbol, company_name)
    if not toks:
        return 0.0
    low = (title or "").lower()
    hits = sum(1 for t in toks if t in low)
    if hits == 0:
        return 0.0
    # Any direct hit is meaningful; full-name match scores higher.
    return min(1.0, 0.5 + 0.5 * (hits / len(toks)))
