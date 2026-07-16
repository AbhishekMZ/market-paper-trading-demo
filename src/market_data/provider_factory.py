"""Factory: build the configured MarketDataProvider by name.

Strategy code never calls this — only the orchestrator (main.py) does, once,
based on config/settings.yml -> market_data.provider.
"""
from __future__ import annotations

from typing import Any, Dict

from market_data.base import MarketDataProvider


def build_market_data_provider(
    provider_name: str,
    rate_limits: Dict[str, Any] | None = None,
    fetch_company_info: bool = True,
) -> MarketDataProvider:
    rate_limits = rate_limits or {}
    sleep = float(rate_limits.get("sleep_seconds_between_symbols", 1))
    retries = int(rate_limits.get("max_retries", 2))
    normalized = (provider_name or "yfinance").strip().lower()

    if normalized in {"yahoo", "yfinance", "yahoo_finance"}:
        from market_data.yahoo_finance_provider import YahooFinanceProvider

        return YahooFinanceProvider(
            sleep_seconds=sleep, max_retries=retries, fetch_company_info=fetch_company_info
        )

    if normalized in {"yahooquery"}:
        from market_data.yahooquery_provider import YahooQueryProvider

        return YahooQueryProvider()

    if normalized in {"serpapi", "google_finance"}:
        raise RuntimeError(
            "SerpApi provider is disabled. Use market_data.provider: yfinance in config/settings.yml."
        )

    raise ValueError(f"Unsupported market data provider: {provider_name!r}")
