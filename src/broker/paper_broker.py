"""PaperBrokerAdapter — the only ENABLED adapter in v1.

Fully simulates equity-delivery paper trades against JSON state. It never
touches a real broker API and requires no credentials.

Responsibilities (execution only — NO strategy logic):
  * Simulate paper buys / sells / partial trims
  * Maintain fake cash, fake holdings, realized P&L
  * Refuse orders that violate hard safety rules (backstop to risk_engine)
  * Mark every order is_paper=True
  * Return realistic OrderResult objects

Mark-to-market valuation (last_price / unrealized P&L) is performed by
portfolio_manager, keeping this adapter focused on the order ledger.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import storage
from broker.base import BrokerAdapter, BrokerError
from order_models import (
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderState,
    OrderStatus,
    ProductType,
)
from utils import gen_id, now_ist_iso


def _default_portfolio(starting_capital: float) -> Dict[str, Any]:
    return {
        "as_of": now_ist_iso(),
        "starting_capital": starting_capital,
        "monthly_capital": starting_capital,
        "cash": starting_capital,
        "holdings_value": 0.0,
        "total_value": starting_capital,
        "realized_pnl": 0.0,
        "unrealized_pnl": 0.0,
        "positions": [],
        "closed_positions": [],
    }


class PaperBrokerAdapter(BrokerAdapter):
    name = "paper"
    is_paper = True

    def __init__(
        self,
        starting_capital: float = 10000.0,
        max_trade_amount: float = 2000.0,
        price_provider: Optional[Callable[[str], Optional[float]]] = None,
    ) -> None:
        self.starting_capital = starting_capital
        self.max_trade_amount = max_trade_amount
        self._price_provider = price_provider
        self._prices: Dict[str, float] = {}
        # Ensure a portfolio file exists.
        if not storage.load_state("portfolio"):
            storage.save_state("portfolio", _default_portfolio(starting_capital))

    # ------------------------------------------------------------------ #
    # Price wiring (set by the execution layer from market data)
    # ------------------------------------------------------------------ #
    def set_prices(self, prices: Dict[str, float]) -> None:
        self._prices.update({k: v for k, v in prices.items() if v is not None})

    def get_ltp(self, symbol: str) -> Optional[float]:
        if symbol in self._prices:
            return self._prices[symbol]
        if self._price_provider:
            return self._price_provider(symbol)
        return None

    # ------------------------------------------------------------------ #
    # Account / portfolio
    # ------------------------------------------------------------------ #
    def _portfolio(self) -> Dict[str, Any]:
        return storage.load_state("portfolio", _default_portfolio(self.starting_capital))

    def get_account_profile(self) -> Dict[str, Any]:
        return {
            "broker": self.name,
            "mode": "PAPER",
            "is_paper": True,
            "client": "paper-account",
            "currency": "INR",
        }

    def get_cash_balance(self) -> float:
        return float(self._portfolio().get("cash", 0.0))

    def get_holdings(self) -> List[Dict[str, Any]]:
        return list(self._portfolio().get("positions", []))

    def get_positions(self) -> List[Dict[str, Any]]:
        # For equity delivery paper trading, positions mirror holdings.
        return self.get_holdings()

    # ------------------------------------------------------------------ #
    # Orders
    # ------------------------------------------------------------------ #
    def place_order(self, order_request: OrderRequest) -> OrderResult:
        # Hard backstop checks (risk_engine is the primary gate).
        if not order_request.is_paper:
            return self._rejected(order_request, "Adapter is paper-only; real orders are blocked.")
        if order_request.product_type != ProductType.DELIVERY:
            return self._rejected(order_request, "Only DELIVERY product type is allowed.")
        if order_request.amount > self.max_trade_amount + 1e-6:
            return self._rejected(
                order_request,
                f"Amount {order_request.amount} exceeds max per trade {self.max_trade_amount}.",
            )

        if order_request.side == OrderSide.BUY:
            return self._execute_buy(order_request)
        return self._execute_sell(order_request)

    def _execute_buy(self, req: OrderRequest) -> OrderResult:
        pf = self._portfolio()
        fill_price = float(req.limit_price)
        cost = fill_price * req.quantity
        if cost > pf.get("cash", 0.0) + 1e-6:
            return self._rejected(req, f"Insufficient fake cash: need {cost:.2f}, have {pf['cash']:.2f}.")

        pf["cash"] = round(pf["cash"] - cost, 2)
        positions = pf.setdefault("positions", [])
        existing = next((p for p in positions if p["symbol"] == req.symbol), None)
        if existing:
            # Increase an existing position (averaging up). Averaging *down*
            # is blocked upstream in risk_engine.
            total_qty = existing["quantity"] + req.quantity
            total_cost = existing["invested"] + cost
            existing["quantity"] = total_qty
            existing["invested"] = round(total_cost, 2)
            existing["avg_price"] = round(total_cost / total_qty, 4)
        else:
            positions.append(
                {
                    "symbol": req.symbol,
                    "exchange": req.exchange,
                    "name": req.symbol,
                    "quantity": req.quantity,
                    "avg_price": round(fill_price, 4),
                    "invested": round(cost, 2),
                    "last_price": fill_price,
                    "current_value": round(cost, 2),
                    "unrealized_pnl": 0.0,
                    "unrealized_pnl_pct": 0.0,
                    "bot_owned": True,
                    "opened_at": now_ist_iso(),
                    "signal_id": req.generated_by_signal_id,
                    "risk_status": "OK",
                }
            )
        pf["as_of"] = now_ist_iso()
        storage.save_state("portfolio", pf)

        result = OrderResult(
            order_id=req.order_id,
            symbol=req.symbol,
            side=OrderSide.BUY,
            status=OrderState.FILLED,
            quantity=req.quantity,
            filled_quantity=req.quantity,
            price=fill_price,
            amount=round(cost, 2),
            is_paper=True,
            broker_adapter=self.name,
            message="Paper BUY filled at limit price.",
            reason=req.reason,
            signal_id=req.generated_by_signal_id,
        )
        self._record_trade(result)
        return result

    def _execute_sell(self, req: OrderRequest) -> OrderResult:
        pf = self._portfolio()
        positions = pf.setdefault("positions", [])
        pos = next((p for p in positions if p["symbol"] == req.symbol), None)
        if pos is None:
            return self._rejected(req, "No paper position to sell (sell scope is bot-owned only).")
        if not pos.get("bot_owned", False):
            return self._rejected(req, "Position is not bot-owned; selling is not allowed.")
        if req.quantity > pos["quantity"]:
            return self._rejected(
                req, f"Sell qty {req.quantity} exceeds held qty {pos['quantity']}."
            )

        fill_price = float(req.limit_price)
        proceeds = fill_price * req.quantity
        cost_basis = pos["avg_price"] * req.quantity
        realized = round(proceeds - cost_basis, 2)

        pf["cash"] = round(pf.get("cash", 0.0) + proceeds, 2)
        pf["realized_pnl"] = round(pf.get("realized_pnl", 0.0) + realized, 2)

        is_full_exit = req.quantity == pos["quantity"]
        if is_full_exit:
            positions.remove(pos)
            pf.setdefault("closed_positions", []).append(
                {
                    "symbol": pos["symbol"],
                    "exchange": pos.get("exchange", "NSE"),
                    "quantity": req.quantity,
                    "avg_price": pos["avg_price"],
                    "exit_price": fill_price,
                    "realized_pnl": realized,
                    "realized_pnl_pct": round((fill_price / pos["avg_price"] - 1) * 100, 2)
                    if pos["avg_price"]
                    else 0.0,
                    "opened_at": pos.get("opened_at"),
                    "closed_at": now_ist_iso(),
                    "bot_owned": True,
                    "reason": req.reason,
                }
            )
        else:
            pos["quantity"] -= req.quantity
            pos["invested"] = round(pos["avg_price"] * pos["quantity"], 2)

        pf["as_of"] = now_ist_iso()
        storage.save_state("portfolio", pf)

        result = OrderResult(
            order_id=req.order_id,
            symbol=req.symbol,
            side=OrderSide.SELL,
            status=OrderState.FILLED,
            quantity=req.quantity,
            filled_quantity=req.quantity,
            price=fill_price,
            amount=round(proceeds, 2),
            is_paper=True,
            broker_adapter=self.name,
            message=("Paper EXIT filled." if is_full_exit else "Paper TRIM filled."),
            reason=req.reason,
            signal_id=req.generated_by_signal_id,
        )
        self._record_trade(result, realized_pnl=realized)
        return result

    def _rejected(self, req: OrderRequest, message: str) -> OrderResult:
        result = OrderResult(
            order_id=req.order_id,
            symbol=req.symbol,
            side=req.side,
            status=OrderState.REJECTED,
            quantity=req.quantity,
            filled_quantity=0,
            price=req.limit_price,
            amount=req.amount,
            is_paper=True,
            broker_adapter=self.name,
            message=message,
            reason=req.reason,
            signal_id=req.generated_by_signal_id,
        )
        self._record_trade(result)
        return result

    # ------------------------------------------------------------------ #
    # Order/trade books
    # ------------------------------------------------------------------ #
    def _record_trade(self, result: OrderResult, realized_pnl: float = 0.0) -> None:
        history = storage.load_state("trade_history", [])
        if not isinstance(history, list):
            history = []
        entry = result.to_dict()
        entry["realized_pnl"] = realized_pnl
        history.append(entry)
        storage.save_state("trade_history", history)

    def modify_order(self, order_id: str, updates: Dict[str, Any]) -> OrderResult:
        # Paper trades fill instantly, so there is nothing pending to modify.
        raise BrokerError("Paper orders fill instantly; modify_order is not applicable.")

    def cancel_order(self, order_id: str) -> OrderResult:
        raise BrokerError("Paper orders fill instantly; cancel_order is not applicable.")

    def get_order_status(self, order_id: str) -> OrderStatus:
        history = storage.load_state("trade_history", [])
        for entry in history if isinstance(history, list) else []:
            if entry.get("order_id") == order_id:
                return OrderStatus(
                    order_id=order_id,
                    status=OrderState(entry.get("status", "FILLED")),
                    filled_quantity=entry.get("filled_quantity", 0),
                    average_price=entry.get("price"),
                    message=entry.get("message", ""),
                )
        return OrderStatus(order_id=order_id, status=OrderState.REJECTED, message="Unknown order id.")

    def get_order_book(self) -> List[Dict[str, Any]]:
        history = storage.load_state("trade_history", [])
        return list(history) if isinstance(history, list) else []

    def get_trade_book(self) -> List[Dict[str, Any]]:
        history = storage.load_state("trade_history", [])
        return [t for t in history if t.get("status") == "FILLED"] if isinstance(history, list) else []
