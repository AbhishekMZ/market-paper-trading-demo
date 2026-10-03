"""NewsEventRiskStrategy — score the SAME enriched items the risk overlay uses.

The plugin does not read a second yfinance title list. Callers pass the items
`NewsRiskEngine.collect_items` already relevance-filtered and scored
(`context["news_items"]` or `context["news_items_by_symbol"][symbol]`).

No relevant items → this strategy does not contribute. Absence of news is not
a neutral 65. Positive news can still nudge the score (capped in config); the
overlay remains the only path that downgrades a buy, and it never creates one.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from news.base import NewsItem
from news.sentiment import aggregate
from strategy.base import NEGATIVE, NEUTRAL, StrategyPlugin, StrategyResult


def _items_for(context: Dict[str, Any], symbol: str) -> List[Any]:
    if not isinstance(context, dict):
        return []
    if "news_items" in context:
        return list(context.get("news_items") or [])
    by_symbol = context.get("news_items_by_symbol")
    if isinstance(by_symbol, dict) and symbol in by_symbol:
        return list(by_symbol.get(symbol) or [])
    return []


def _record(item: Any) -> Optional[Tuple[float, float, str, float, Optional[float]]]:
    """(polarity, confidence, provider, relevance, age_hours) from an enriched item."""
    if isinstance(item, NewsItem):
        return (
            float(item.sentiment_score or 0.0),
            float(item.sentiment_confidence or 0.0),
            str(item.provider or "item"),
            float(item.relevance or 0.0),
            item.age_hours,
        )
    if isinstance(item, dict) and ("sentiment_score" in item or "sentiment_confidence" in item):
        age = item.get("age_hours")
        try:
            age_f = float(age) if age is not None else None
        except (TypeError, ValueError):
            age_f = None
        return (
            float(item.get("sentiment_score") or 0.0),
            float(item.get("sentiment_confidence") or 0.0),
            str(item.get("provider") or "item"),
            float(item.get("relevance") if item.get("relevance") is not None else 1.0),
            age_f,
        )
    return None


class NewsEventRiskStrategy(StrategyPlugin):
    def name(self) -> str:
        return "news_event_risk"

    def describe(self) -> str:
        return "Finance-aware sentiment on the risk engine's articles; missing news does not score."

    def required_fields(self) -> List[str]:
        return []  # items come from context, not the price snapshot

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        cfg = (context or {}).get("news_cfg") or {}
        items = _items_for(context or {}, symbol)
        records = [r for r in (_record(it) for it in items) if r is not None]

        if not records:
            return StrategyResult(
                strategy_name=self.name(),
                score_contribution=50.0,
                confidence=0.0,
                signal=NEUTRAL,
                reason="No relevant news; excluded from the score (absence is not a neutral read).",
                data_used={"items_used": 0},
                warnings=["No relevant news; strategy does not contribute."],
                is_valid=False,
                contributes_to_score=False,
                display_only=True,
            )

        agg = aggregate(records, cfg)
        ps = (cfg.get("sentiment") or {}).get("plugin_scoring") or {}
        neutral_base = float(ps.get("neutral_base", 65))
        max_pos = float(ps.get("max_positive", 78))
        min_neg = float(ps.get("min_negative", 25))

        effective = agg.polarity * agg.confidence
        if effective >= 0:
            score = neutral_base + effective * (max_pos - neutral_base)
        else:
            score = neutral_base + effective * (neutral_base - min_neg)
        score = max(0.0, min(100.0, score))

        signal = agg.label.value
        risk_flags = ["news:negative_sentiment"] if signal == NEGATIVE else []

        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=max(0.2, round(agg.confidence, 2)),
            signal=signal,
            reason=(f"Scored {len(records)} shared news item(s). Sentiment {signal} "
                    f"(polarity {agg.polarity:.2f}, confidence {agg.confidence:.2f}) "
                    f"-> {score:.0f}/100."),
            data_used={"items_used": len(records),
                       "polarity": agg.polarity,
                       "confidence": agg.confidence,
                       "providers": sorted({r[2] for r in records})},
            warnings=[],
            risk_flags=risk_flags,
        )
