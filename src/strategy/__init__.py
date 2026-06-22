"""Modular strategy layer.

Strategies are plugins (see base.StrategyPlugin) that produce evidence and a
0-100 score contribution. The HybridSignalEngine combines them into one
explainable signal. No strategy places trades directly.
"""
from __future__ import annotations

from strategy.base import StrategyPlugin, StrategyResult
from strategy.hybrid_signal_engine import HybridSignalEngine
from strategy.market_regime import MarketRegimeEngine, RegimeResult
from strategy.research_registry import ResearchRegistry
from strategy.strategy_evaluator import StrategyEvaluator

__all__ = [
    "StrategyPlugin",
    "StrategyResult",
    "HybridSignalEngine",
    "MarketRegimeEngine",
    "RegimeResult",
    "ResearchRegistry",
    "StrategyEvaluator",
]
