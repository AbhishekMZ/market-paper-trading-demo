"""Quick manual test for the Yahoo Finance provider.

Run:  python scripts/test_yfinance_provider.py
Requires internet access (yfinance hits Yahoo's public endpoints).

Expected:
  - quote should not be None and current_price should exist
  - history should have multiple bars
  - news may be empty (that's OK)
  - if data_quality.is_usable is False, the strategy engine SKIPS that symbol
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from market_data.yahoo_finance_provider import YahooFinanceProvider  # noqa: E402

provider = YahooFinanceProvider(sleep_seconds=1, max_retries=2)
symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "^NSEI"]

for symbol in symbols:
    snap = provider.get_snapshot(symbol)
    print("=" * 80)
    print(symbol)
    print("quote:", snap.quote)
    print("bars:", len(snap.history))
    print("news:", len(snap.news))
    print("quality:", snap.data_quality)
