"""Backtesting / validation package.

v1 ships a lightweight PAPER-TRADE REPLAY evaluator (backtest_engine) and a
walk-forward validator SKELETON. It deliberately does NOT fabricate historical
backtest results — honest placeholders are preferred over fake profitability.
The CostModel is real and used by reports for cost-adjusted P&L.
"""
from __future__ import annotations

from backtesting.cost_model import CostModel

__all__ = ["CostModel"]
