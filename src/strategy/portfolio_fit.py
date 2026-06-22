"""PortfolioFitStrategy — respect the fake budget, holdings, and limits.

This strategy informs the score and surfaces warnings, but the AUTHORITATIVE
hard gate is still risk_engine.py at execution time. Here we discourage buys
that would break budget/limits and encourage diversification.
"""
from __future__ import annotations

from typing import Any, Dict, List

from strategy.base import NEGATIVE, NEUTRAL, POSITIVE, StrategyPlugin, StrategyResult


class PortfolioFitStrategy(StrategyPlugin):
    def name(self) -> str:
        return "portfolio_fit"

    def describe(self) -> str:
        return "Checks fit against the monthly fake budget, current holdings, and per-day/month buy limits."

    def required_fields(self) -> List[str]:
        return []

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        budget = context.get("budget", {})
        limits = context.get("limits", {})
        held_symbols = context.get("held_symbols", [])
        buys_today = context.get("buys_today", 0)
        price = market_data.get("price")

        max_trade = float(limits.get("max_trade_amount", 2000))
        max_buys_day = int(limits.get("max_buys_per_day", 1))
        max_buys_month = int(limits.get("max_buys_per_month", 5))
        capital_remaining = float(budget.get("capital_remaining", 0.0))
        buys_this_month = int(budget.get("buys_this_month", 0))

        warnings: List[str] = []
        risk_flags: List[str] = []
        score = 80.0
        signal = POSITIVE

        if symbol in held_symbols:
            score -= 45.0
            risk_flags.append("already_held")
            warnings.append("Already held — adding would require averaging (blocked) and reduces diversification.")
        if capital_remaining < max_trade:
            # Can we still afford at least one share?
            if price and capital_remaining >= price:
                score -= 10.0
                warnings.append("Limited monthly budget remaining.")
            else:
                score = 10.0
                risk_flags.append("monthly_budget_exhausted")
                warnings.append("Monthly fake budget exhausted — no new buys.")
        if buys_today >= max_buys_day:
            score = min(score, 15.0)
            risk_flags.append("daily_buy_limit_reached")
            warnings.append("Daily buy limit reached.")
        if buys_this_month >= max_buys_month:
            score = min(score, 10.0)
            risk_flags.append("monthly_buy_limit_reached")
            warnings.append("Monthly buy limit reached.")
        if price and price > max_trade:
            score = min(score, 20.0)
            risk_flags.append("price_above_per_trade_cap")
            warnings.append(f"Share price ₹{price:.0f} exceeds per-trade cap ₹{max_trade:.0f}.")

        score = max(0.0, min(100.0, score))
        if score <= 40:
            signal = NEGATIVE
        elif score < 60:
            signal = NEUTRAL

        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=0.7,
            signal=signal,
            reason=(
                f"Fit {score:.0f}/100 — budget ₹{capital_remaining:.0f} left, "
                f"{buys_this_month}/{max_buys_month} monthly buys used, held={symbol in held_symbols}."
            ),
            data_used={"capital_remaining": capital_remaining, "buys_this_month": buys_this_month,
                       "buys_today": buys_today, "already_held": symbol in held_symbols},
            warnings=warnings,
            risk_flags=risk_flags,
        )
