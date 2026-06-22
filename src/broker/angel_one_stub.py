"""AngelOneBrokerAdapter — DISABLED STUB (v1).

================================ READ ME ================================
This adapter is intentionally INERT in v1. It exists only to prove that
the broker interface is real-broker-ready and to mark exactly where a
future SmartAPI integration would slot in.

In v1 this adapter:
  * performs NO network calls
  * asks for NO credentials
  * places NO real orders
  * raises DisabledBrokerError for every live method
  * stays disabled by config (broker.yml: angel_one_enabled=false)

DO NOT implement live order placement here as part of v1. Enabling real
trading is a deliberate, multi-step future task gated by the safety
confirmations in broker.yml and the checklist in
docs/future_real_trading_transition.md.
========================================================================
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from broker.base import BrokerAdapter, DisabledBrokerError
from order_models import OrderRequest, OrderResult, OrderStatus

_DISABLED_MSG = (
    "AngelOneBrokerAdapter is disabled in v1. Real Angel One execution is "
    "intentionally not implemented. See docs/future_real_trading_transition.md."
)


class AngelOneBrokerAdapter(BrokerAdapter):
    name = "angel_one"
    is_paper = False  # would be a REAL broker — hence disabled in v1

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # NOTE: No credentials are accepted or read here in v1.
        # FUTURE: a real implementation would accept a config object and
        # construct a SmartAPI session lazily (never at import time):
        #
        #   from SmartApi import SmartConnect            # pip dependency, future only
        #   self._client = None                          # created on first authenticate()
        #   self._api_key = os.environ["ANGEL_ONE_API_KEY"]
        #
        # All of that is deliberately omitted in v1.
        self._enabled = False

    # ------------------------------------------------------------------ #
    # FUTURE: authentication (intentionally not implemented in v1)
    # ------------------------------------------------------------------ #
    def authenticate(self) -> None:
        # TODO (future phase): implement SmartAPI login using TOTP.
        #   - read ANGEL_ONE_CLIENT_ID / PASSWORD / TOTP_SECRET / API_KEY from env
        #   - totp = pyotp.TOTP(totp_secret).now()
        #   - session = SmartConnect(api_key=...).generateSession(client_id, password, totp)
        #   - store jwt/feed/refresh tokens in memory only (never on disk/git)
        raise DisabledBrokerError(_DISABLED_MSG)

    # ------------------------------------------------------------------ #
    # account / portfolio  (all disabled in v1)
    # ------------------------------------------------------------------ #
    def get_account_profile(self) -> Dict[str, Any]:
        # TODO (future): SmartConnect.getProfile(refresh_token)
        raise DisabledBrokerError(_DISABLED_MSG)

    def get_cash_balance(self) -> float:
        # TODO (future): SmartConnect.rmsLimit() -> available cash
        raise DisabledBrokerError(_DISABLED_MSG)

    def get_holdings(self) -> List[Dict[str, Any]]:
        # TODO (future): SmartConnect.holding()
        raise DisabledBrokerError(_DISABLED_MSG)

    def get_positions(self) -> List[Dict[str, Any]]:
        # TODO (future): SmartConnect.position()
        raise DisabledBrokerError(_DISABLED_MSG)

    # ------------------------------------------------------------------ #
    # market data  (disabled in v1)
    # ------------------------------------------------------------------ #
    def get_ltp(self, symbol: str) -> Optional[float]:
        # TODO (future): SmartConnect.ltpData(exchange, tradingsymbol, symboltoken)
        raise DisabledBrokerError(_DISABLED_MSG)

    # ------------------------------------------------------------------ #
    # order lifecycle  (disabled in v1)
    # ------------------------------------------------------------------ #
    def place_order(self, order_request: OrderRequest) -> OrderResult:
        # TODO (future): build SmartAPI order params (DELIVERY + LIMIT only),
        # call SmartConnect.placeOrder(...), then map the response to OrderResult.
        # MUST remain gated behind manual approval + safety confirmations.
        raise DisabledBrokerError(_DISABLED_MSG)

    def modify_order(self, order_id: str, updates: Dict[str, Any]) -> OrderResult:
        # TODO (future): SmartConnect.modifyOrder(...)
        raise DisabledBrokerError(_DISABLED_MSG)

    def cancel_order(self, order_id: str) -> OrderResult:
        # TODO (future): SmartConnect.cancelOrder(...)
        raise DisabledBrokerError(_DISABLED_MSG)

    def get_order_status(self, order_id: str) -> OrderStatus:
        # TODO (future): SmartConnect.orderBook() lookup by order id
        raise DisabledBrokerError(_DISABLED_MSG)

    def get_order_book(self) -> List[Dict[str, Any]]:
        # TODO (future): SmartConnect.orderBook()
        raise DisabledBrokerError(_DISABLED_MSG)

    def get_trade_book(self) -> List[Dict[str, Any]]:
        # TODO (future): SmartConnect.tradeBook()
        raise DisabledBrokerError(_DISABLED_MSG)
