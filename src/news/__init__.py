"""News risk layer — a post-strategy RISK overlay for the paper-trading system.

Public surface:
    NewsRiskEngine        — assess(symbol,…) -> NewsRiskAssessment; apply_to_signal(); build_alert()
    NewsRiskAssessment    — per-symbol verdict
    NewsItem              — one normalized article
    NewsSentiment / NewsRiskLevel / NewsEventType — enums

Design invariant: news can only ADD caution. It blocks/downgrades paper buys; it
never creates or upgrades one. See news_risk_engine.py for the enforced rules.
"""
from __future__ import annotations

from news.base import (
    NewsEventType,
    NewsItem,
    NewsProvider,
    NewsRiskAssessment,
    NewsRiskLevel,
    NewsSentiment,
)
from news.news_risk_engine import NewsRiskEngine

__all__ = [
    "NewsRiskEngine",
    "NewsRiskAssessment",
    "NewsItem",
    "NewsProvider",
    "NewsSentiment",
    "NewsRiskLevel",
    "NewsEventType",
]
