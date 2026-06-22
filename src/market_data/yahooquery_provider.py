"""YahooQueryProvider — OPTIONAL future provider (skeleton, not used in v1).

`yahooquery` is another UNOFFICIAL Yahoo Finance wrapper. It exposes more
front-end Yahoo modules (richer fundamentals / news-style data) and can be a
useful fallback or upgrade later. It is intentionally NOT implemented in v1 to
keep the dependency surface small.

To enable later:
  1. add `yahooquery` to requirements.txt
  2. implement get_snapshot/get_many_snapshots below (map Ticker(...).price,
     .history(...), .news into MarketSnapshot)
  3. register it in provider_factory.build_market_data_provider
"""
from __future__ import annotations

from typing import List

from market_data.base import MarketDataProvider, MarketSnapshot


class YahooQueryProvider(MarketDataProvider):
    provider_name = "yahooquery"

    def get_snapshot(self, symbol: str, period: str = "1mo", interval: str = "1d") -> MarketSnapshot:
        raise NotImplementedError(
            "YahooQueryProvider is a documented future option and is not implemented in v1. "
            "Use provider: yfinance."
        )

    def get_many_snapshots(self, symbols: List[str], period: str = "1mo", interval: str = "1d"):
        raise NotImplementedError(
            "YahooQueryProvider is a documented future option and is not implemented in v1."
        )
