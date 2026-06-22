"""Lightweight paper-trade replay (NOT a historical backtester).

v1 scope: replay the trades the system ACTUALLY made on paper and compute
cost-adjusted outcomes. This is honest — it only summarizes recorded paper
activity. It does NOT simulate the strategy over historical price data
(that would require a clean, survivorship-bias-free price history we do not
have on the SerpApi free tier).

A full historical backtester is intentionally left as a documented placeholder
(see replay_full_history) so we never present fabricated profitability.
"""
from __future__ import annotations

from typing import Any, Dict, List

import storage
from backtesting.cost_model import CostModel


class PaperTradeReplay:
    def __init__(self, cost_model: CostModel) -> None:
        self.cost_model = cost_model

    def summarize(self) -> Dict[str, Any]:
        """Summarize realized paper trades with estimated costs applied."""
        trades = storage.load_state("trade_history", [])
        portfolio = storage.load_state("portfolio", {})
        if not isinstance(trades, list):
            trades = []

        closed = portfolio.get("closed_positions", [])
        gross_realized = sum(float(c.get("realized_pnl", 0.0)) for c in closed)

        est_costs = 0.0
        for c in closed:
            amount = float(c.get("avg_price", 0)) * float(c.get("quantity", 0))
            est_costs += self.cost_model.round_trip_cost(amount)

        wins = [c for c in closed if float(c.get("realized_pnl", 0.0)) >= 0]
        losses = [c for c in closed if float(c.get("realized_pnl", 0.0)) < 0]
        net_realized = round(gross_realized - est_costs, 2)

        return {
            "closed_trades": len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate_pct": round(len(wins) / len(closed) * 100, 1) if closed else 0.0,
            "gross_realized_pnl": round(gross_realized, 2),
            "estimated_costs": round(est_costs, 2),
            "net_realized_pnl_cost_adjusted": net_realized,
            "best_trade": max((float(c.get("realized_pnl", 0.0)) for c in closed), default=0.0),
            "worst_trade": min((float(c.get("realized_pnl", 0.0)) for c in closed), default=0.0),
        }

    def replay_full_history(self, *args: Any, **kwargs: Any) -> None:
        """PLACEHOLDER (intentionally not implemented in v1).

        A real historical backtest must address survivorship bias, look-ahead
        bias, point-in-time fundamentals, corporate actions, and realistic
        fills. Implementing it badly is worse than not at all. See
        docs/strategy_validation_principles.md before building this.
        """
        raise NotImplementedError(
            "Historical backtesting is a documented placeholder in v1. "
            "See docs/strategy_validation_principles.md."
        )
