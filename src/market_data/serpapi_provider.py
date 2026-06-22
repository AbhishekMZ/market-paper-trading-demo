"""SerpApiProvider — DISABLED (kept only as a fallback option marker).

SerpApi Google Finance was the original v1 data source but is disabled now:
the project uses Yahoo Finance via yfinance (no API key, no free-tier quota).
This stub remains so provider_factory can give a clear message if someone
configures `provider: serpapi`, and so a future fallback could be re-added.
"""
from __future__ import annotations

from typing import List

from market_data.base import MarketDataProvider, MarketSnapshot


class SerpApiProvider(MarketDataProvider):
    provider_name = "serpapi"

    def get_snapshot(self, symbol: str, period: str = "1mo", interval: str = "1d") -> MarketSnapshot:
        raise RuntimeError(
            "SerpApi provider is disabled. Set market_data.provider: yfinance in config/settings.yml."
        )

    def get_many_snapshots(self, symbols: List[str], period: str = "1mo", interval: str = "1d"):
        raise RuntimeError(
            "SerpApi provider is disabled. Set market_data.provider: yfinance in config/settings.yml."
        )
