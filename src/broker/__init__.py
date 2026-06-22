"""Broker adapters package.

Public surface: the abstract BrokerAdapter and a small factory that returns
the configured adapter. In v1 only the paper adapter can be constructed in an
enabled state; requesting angel_one returns the disabled stub.
"""
from __future__ import annotations

from typing import Any, Optional

from broker.angel_one_stub import AngelOneBrokerAdapter
from broker.base import BrokerAdapter, BrokerError, DisabledBrokerError
from broker.paper_broker import PaperBrokerAdapter

__all__ = [
    "BrokerAdapter",
    "BrokerError",
    "DisabledBrokerError",
    "PaperBrokerAdapter",
    "AngelOneBrokerAdapter",
    "build_adapter",
]


def build_adapter(name: str, **kwargs: Any) -> BrokerAdapter:
    """Return a broker adapter by name.

    Only "paper" is enabled in v1. "angel_one" returns the disabled stub
    (its methods raise DisabledBrokerError). Mode/flag enforcement happens
    in execution_engine before this is ever called for a real broker.
    """
    name = (name or "paper").lower()
    if name == "paper":
        return PaperBrokerAdapter(**kwargs)
    if name == "angel_one":
        return AngelOneBrokerAdapter()
    raise BrokerError(f"Unknown broker adapter: {name!r}")
