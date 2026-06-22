"""NewsEventRiskStrategy — reduce score for negative news / event risk.

Uses headlines returned alongside the SerpApi Google Finance result (no extra
API call, to protect quota). Headlines are scanned with simple keyword
categories. Headlines are NOT over-trusted: positive news lifts the score only
mildly, negative news / risk keywords reduce it more firmly.
"""
from __future__ import annotations

from typing import Any, Dict, List

from strategy.base import NEGATIVE, NEUTRAL, POSITIVE, StrategyPlugin, StrategyResult

NEGATIVE_KEYWORDS = [
    "fraud", "probe", "investigation", "penalty", "downgrade", "weak results",
    "loss", "default", "resignation", "regulatory action", "lawsuit", "debt concern",
    "raid", "scam", "ban", "fine", "recall", "miss",
]
POSITIVE_KEYWORDS = [
    "strong results", "order win", "expansion", "approval", "upgrade",
    "margin improvement", "debt reduction", "record", "beats", "wins order",
]


class NewsEventRiskStrategy(StrategyPlugin):
    def name(self) -> str:
        return "news_event_risk"

    def describe(self) -> str:
        return "Scans available headlines for risk/positive keywords; reduces score on negative news."

    def required_fields(self) -> List[str]:
        return []  # degrades gracefully when no news is present

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        headlines: List[str] = market_data.get("headlines", []) or []
        warnings: List[str] = []
        risk_flags: List[str] = []

        if not headlines:
            warnings.append("No news data available; using a neutral assumption.")
            return StrategyResult(
                strategy_name=self.name(),
                score_contribution=65.0,            # neutral-ish, not optimistic
                confidence=0.25,
                signal=NEUTRAL,
                reason="No headlines available; assuming no adverse news (low confidence).",
                data_used={"headlines_used": 0},
                warnings=warnings,
            )

        neg_hits, pos_hits = [], []
        for h in headlines:
            low = h.lower()
            for kw in NEGATIVE_KEYWORDS:
                if kw in low:
                    neg_hits.append(kw)
                    risk_flags.append(f"news:{kw}")
            for kw in POSITIVE_KEYWORDS:
                if kw in low:
                    pos_hits.append(kw)

        # Negative news weighs more heavily than positive (do not over-trust).
        score = 65.0 - 12.0 * len(set(neg_hits)) + 5.0 * len(set(pos_hits))
        score = max(0.0, min(100.0, score))
        if neg_hits:
            signal = NEGATIVE
        elif pos_hits:
            signal = POSITIVE
        else:
            signal = NEUTRAL

        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=0.55,
            signal=signal,
            reason=(
                f"Scanned {len(headlines)} headlines. "
                f"Negative: {sorted(set(neg_hits)) or 'none'}; positive: {sorted(set(pos_hits)) or 'none'}."
            ),
            data_used={"headlines_used": len(headlines),
                       "negative_keywords": sorted(set(neg_hits)),
                       "positive_keywords": sorted(set(pos_hits))},
            warnings=warnings,
            risk_flags=sorted(set(risk_flags)),
        )
