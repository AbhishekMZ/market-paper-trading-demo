"""NewsEventRiskStrategy — reduce/raise score using the shared sentiment scorer.

Scores each available headline with the finance-aware scorer, aggregates, and
maps polarity × confidence onto the 0-100 contribution. Low-confidence reads stay
near neutral, so a single noisy headline no longer swings the score. Negative news
weighs more heavily than positive (caution-first). Degrades to neutral with no news.
"""
from __future__ import annotations

from typing import Any, Dict, List

from news.sentiment import aggregate, score_text
from strategy.base import NEGATIVE, NEUTRAL, POSITIVE, StrategyPlugin, StrategyResult


class NewsEventRiskStrategy(StrategyPlugin):
    def name(self) -> str:
        return "news_event_risk"

    def describe(self) -> str:
        return "Finance-aware headline sentiment; confidence-damped score contribution."

    def required_fields(self) -> List[str]:
        return []  # degrades gracefully when no news is present

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        headlines: List[str] = market_data.get("headlines", []) or []
        cfg = context.get("news_cfg") or {}

        if not headlines:
            return StrategyResult(
                strategy_name=self.name(),
                score_contribution=65.0,            # neutral-ish, not optimistic
                confidence=0.25,
                signal=NEUTRAL,
                reason="No headlines available; assuming no adverse news (low confidence).",
                data_used={"headlines_used": 0},
                warnings=["No news data available; using a neutral assumption."],
            )

        scores = [score_text(h, cfg) for h in headlines]
        # Treat each headline as a corroborating "voice": multiple headlines that
        # agree raise confidence (and conflicting ones lower it), mirroring the
        # cross-source agreement logic. A single headline => single-source penalty.
        records = [(s.polarity, s.confidence, f"headline_{i}", 1.0, None)
                   for i, s in enumerate(scores)]
        agg = aggregate(records, cfg)

        ps = (cfg.get("sentiment", {}) or {}).get("plugin_scoring", {})
        neutral_base = float(ps.get("neutral_base", 65))
        max_pos = float(ps.get("max_positive", 78))
        min_neg = float(ps.get("min_negative", 25))

        effective = agg.polarity * agg.confidence       # confidence damps the deviation
        if effective >= 0:
            score = neutral_base + effective * (max_pos - neutral_base)
        else:
            score = neutral_base + effective * (neutral_base - min_neg)
        score = max(0.0, min(100.0, score))

        signal = agg.label.value  # "POSITIVE" | "NEUTRAL" | "NEGATIVE"
        risk_flags = ["news:negative_sentiment"] if signal == NEGATIVE else []

        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=max(0.2, round(agg.confidence, 2)),
            signal=signal,
            reason=(f"Scanned {len(headlines)} headline(s). Sentiment {signal} "
                    f"(polarity {agg.polarity:.2f}, confidence {agg.confidence:.2f}) "
                    f"-> {score:.0f}/100."),
            data_used={"headlines_used": len(headlines),
                       "polarity": agg.polarity,
                       "confidence": agg.confidence,
                       "negated_any": any(s.negated for s in scores)},
            warnings=[],
            risk_flags=risk_flags,
        )
