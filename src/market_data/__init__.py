"""Market-data provider abstraction.

Public surface: the normalized models, the provider interface, and the factory.
Strategy code depends on the MODELS only — never on a concrete provider.
"""
from __future__ import annotations

from market_data.base import (
    MarketDataProvider,
    MarketQuote,
    MarketSnapshot,
    PriceBar,
)
from market_data.provider_factory import build_market_data_provider

__all__ = [
    "MarketDataProvider",
    "MarketSnapshot",
    "MarketQuote",
    "PriceBar",
    "build_market_data_provider",
]
