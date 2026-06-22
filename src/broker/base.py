"""Abstract broker interface.

The ENTIRE system talks to this interface — never to a concrete adapter
directly. That is what makes swapping PaperBrokerAdapter for a real
AngelOneBrokerAdapter later a clean, localized change.

RULE: No strategy logic lives in broker adapters. Adapters only execute,
read account/market state, and report results. Scoring, risk decisions,
and mode enforcement live in the engines.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from order_models import OrderRequest, OrderResult, OrderStatus


class BrokerError(Exception):
    """Base class for broker-layer errors."""


class DisabledBrokerError(BrokerError):
    """Raised when a disabled adapter (e.g. Angel One in v1) is invoked."""


class BrokerAdapter(ABC):
    """Common contract every broker adapter must implement."""

    #: Short identifier persisted in trades/audit (e.g. "paper", "angel_one").
    name: str = "base"

    #: Whether this adapter simulates trades (True) or hits a real broker (False).
    is_paper: bool = True

    # ----- account / portfolio -------------------------------------------- #
    @abstractmethod
    def get_account_profile(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def get_cash_balance(self) -> float:
        ...

    @abstractmethod
    def get_holdings(self) -> List[Dict[str, Any]]:
        """Settled delivery holdings."""
        ...

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """Open positions (for paper delivery this mirrors holdings)."""
        ...

    # ----- market data ----------------------------------------------------- #
    @abstractmethod
    def get_ltp(self, symbol: str) -> Optional[float]:
        """Last traded price for a symbol."""
        ...

    # ----- order lifecycle ------------------------------------------------- #
    @abstractmethod
    def place_order(self, order_request: OrderRequest) -> OrderResult:
        ...

    @abstractmethod
    def modify_order(self, order_id: str, updates: Dict[str, Any]) -> OrderResult:
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> OrderResult:
        ...

    @abstractmethod
    def get_order_status(self, order_id: str) -> OrderStatus:
        ...

    @abstractmethod
    def get_order_book(self) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def get_trade_book(self) -> List[Dict[str, Any]]:
        ...
