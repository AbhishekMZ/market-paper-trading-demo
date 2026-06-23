"""Execution engine — the central, broker-agnostic coordinator.

Flow per candidate:
    signal -> (risk gate) -> OrderRequest -> (mode gate) -> adapter.place_order
                                                          -> audit + state update

It contains NO broker-specific code: it only talks to a BrokerAdapter. It also
owns execution_state.json (mode, flags, kill switch, daily buy counter) and
refuses to run on any unsafe configuration.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import storage
from broker.base import BrokerAdapter
from order_models import (
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderState,
    ProductType,
    RiskDecision,
    SignalLabel,
    TradeSignal,
)
from portfolio_manager import PortfolioManager
from risk_engine import RiskEngine
from utils import gen_id, now_ist_iso, today_ist_str


class ExecutionHaltError(RuntimeError):
    """Raised when the configuration is unsafe and the system must not run."""


class ExecutionEngine:
    def __init__(
        self,
        configs: Dict[str, Any],
        adapter: BrokerAdapter,
        risk_engine: RiskEngine,
        portfolio_manager: PortfolioManager,
    ) -> None:
        self.configs = configs
        self.adapter = adapter
        self.risk = risk_engine
        self.pm = portfolio_manager
        self.broker_cfg = configs["broker"].get("broker", {})
        self.exec_cfg = configs["broker"].get("execution", {})
        self.settings = configs["settings"]
        self.max_trade_amount = float(configs["settings"].get("capital", {}).get("max_amount_per_trade", 2000))
        self.require_manual_approval = bool(self.broker_cfg.get("require_manual_approval", True))

    # ------------------------------------------------------------------ #
    # Safety validation — refuse to run on unsafe config
    # ------------------------------------------------------------------ #
    def validate_safety(self) -> List[str]:
        """Raise ExecutionHaltError on any unsafe combination. Returns notes."""
        notes: List[str] = []
        broker = self.broker_cfg
        execu = self.exec_cfg
        adapter_name = broker.get("active_adapter", "paper")
        live = bool(broker.get("live_trading_enabled", False)) or bool(
            self.settings.get("live_trading_enabled", False)
        )
        angel_enabled = bool(broker.get("angel_one_enabled", False))

        # Mode must be in the allowed list.
        mode = execu.get("mode", "paper")
        allowed = execu.get("allowed_modes", ["paper"])
        if mode not in allowed:
            raise ExecutionHaltError(f"Execution mode {mode!r} is not in allowed_modes {allowed}.")

        # 1) live enabled but still on the paper adapter.
        if live and adapter_name == "paper":
            raise ExecutionHaltError(
                "live_trading_enabled=true but broker_adapter is still 'paper'. Refusing to run."
            )
        # 2) angel_one selected but not enabled.
        if adapter_name == "angel_one" and not angel_enabled:
            raise ExecutionHaltError(
                "broker_adapter='angel_one' but angel_one_enabled=false. Refusing to run."
            )
        # 3) angel_one selected but safety confirmations missing.
        if adapter_name == "angel_one":
            confirmations = broker.get("angel_one_safety_confirmations", {})
            missing = [k for k, v in confirmations.items() if not v]
            if missing:
                raise ExecutionHaltError(
                    f"broker_adapter='angel_one' but safety confirmations missing: {missing}."
                )
        # 4) v1 hard rule: only the paper adapter may actually run.
        if adapter_name != "paper":
            raise ExecutionHaltError(
                f"v1 is paper-only. Adapter {adapter_name!r} cannot place orders in v1."
            )
        # 5) real orders must be disabled in v1.
        if broker.get("allow_real_orders", False):
            raise ExecutionHaltError("allow_real_orders=true is not permitted in v1.")

        notes.append(f"Safety OK: mode={mode}, adapter={adapter_name}, live={live}.")
        return notes

    # ------------------------------------------------------------------ #
    # Execution state
    # ------------------------------------------------------------------ #
    def load_state(self) -> Dict[str, Any]:
        state = storage.load_state("execution_state", {})
        broker = self.broker_cfg
        defaults = {
            "mode": self.exec_cfg.get("mode", "paper"),
            "broker_adapter": broker.get("active_adapter", "paper"),
            "live_trading_enabled": bool(broker.get("live_trading_enabled", False)),
            "angel_one_enabled": bool(broker.get("angel_one_enabled", False)),
            "require_manual_approval": self.require_manual_approval,
            "allow_real_orders": bool(broker.get("allow_real_orders", False)),
            "kill_switch": False,
            "buys_today": 0,
            "buy_date": today_ist_str(),
            "last_run": None,
        }
        for k, v in defaults.items():
            state.setdefault(k, v)
        # Reset the daily counter on a new day.
        if state.get("buy_date") != today_ist_str():
            state["buy_date"] = today_ist_str()
            state["buys_today"] = 0
        # Keep config-driven flags authoritative.
        state["broker_adapter"] = broker.get("active_adapter", "paper")
        state["live_trading_enabled"] = bool(broker.get("live_trading_enabled", False))
        state["angel_one_enabled"] = bool(broker.get("angel_one_enabled", False))
        return state

    def save_state(self, state: Dict[str, Any]) -> None:
        state["last_run"] = now_ist_iso()
        storage.save_state("execution_state", state)

    # ------------------------------------------------------------------ #
    # Buy flow
    # ------------------------------------------------------------------ #
    def process_buy(
        self,
        signal: TradeSignal,
        amount_cap: float,
        prices: Dict[str, Optional[float]],
        checkpoint: str = "",
    ) -> Optional[OrderResult]:
        """Attempt a paper BUY for a BUY_SMALL_PAPER signal. Returns result or None."""
        if signal.label != SignalLabel.BUY_SMALL_PAPER:
            return None

        # Defense-in-depth: never buy on anomalous/inconsistent data, even if a
        # bug let the label through. (main also forces NO_ACTION upstream.)
        if signal.data_quality_verdict != "OK" or signal.price_consistency_check == "FAILED":
            self._audit("PAPER_BUY_BLOCKED_BY_DATA_QUALITY", signal.symbol,
                        f"Buy blocked — data quality {signal.data_quality_verdict} "
                        f"(consistency {signal.price_consistency_check}).",
                        {"signal_id": signal.signal_id, "entry_price_used": signal.entry_price_used,
                         "mtm_price_used": signal.mtm_price_used})
            return None

        # Defense-in-depth: never buy into HIGH/CRITICAL adverse news. The news
        # overlay already downgrades the label upstream; this is a backstop.
        if getattr(signal, "news_blocks_buy", False):
            self._audit("PAPER_BUY_BLOCKED_BY_NEWS", signal.symbol,
                        f"Buy blocked — adverse news (risk {signal.news_risk_level}).",
                        {"signal_id": signal.signal_id, "news_event_types": signal.news_event_types,
                         "news_top_headline": signal.news_top_headline})
            return None

        price = prices.get(signal.symbol) or signal.last_price
        if not price or price <= 0:
            self._audit_no_trade(signal, "No usable price to size the order.")
            return None

        # Size the order under the per-trade cap.
        qty = int(amount_cap // price)
        if qty < 1:
            self._audit_no_trade(
                signal, f"Price {price:.2f} exceeds per-trade cap {amount_cap:.0f}; cannot buy 1 share."
            )
            return None
        amount = round(qty * price, 2)

        portfolio = storage.load_state("portfolio", {})
        budget = self.pm.load_budget()
        state = self.load_state()

        decision = self.risk.evaluate_buy(
            signal=signal,
            amount=amount,
            portfolio=portfolio,
            buys_today=state.get("buys_today", 0),
            buys_this_month=budget.get("buys_this_month", 0),
            capital_deployed_this_month=budget.get("capital_deployed", 0.0),
            is_paper=self.adapter.is_paper,
        )
        if not decision.approved:
            self._audit_rejected(signal, decision, amount, qty, price)
            return None

        # Build the order (delivery + limit only — enforced by OrderRequest).
        req = OrderRequest(
            symbol=signal.symbol,
            side=OrderSide.BUY,
            quantity=qty,
            amount=amount,
            limit_price=round(price, 2),
            exchange=signal.exchange,
            product_type=ProductType.DELIVERY,
            reason=signal.reason,
            is_paper=self.adapter.is_paper,
            requires_approval=self._requires_approval(),
            generated_by_signal_id=signal.signal_id,
        )

        # Mode gate: real orders need explicit approval (blocked in v1 anyway).
        if not req.is_paper and self.require_manual_approval:
            self._queue_approval(req, signal)
            self._audit(
                "ORDER_AWAITING_APPROVAL",
                signal.symbol,
                f"Real order queued for manual approval (not executed in v1).",
                {"order_id": req.order_id},
            )
            return None

        result = self.adapter.place_order(req)
        if result.status == OrderState.FILLED:
            state["buys_today"] = state.get("buys_today", 0) + 1
            self.save_state(state)
            self.pm.record_buy(amount)
            self._audit(
                "PAPER_BUY_FILLED",
                signal.symbol,
                f"Bought {qty} @ ₹{price:.2f} (₹{amount:.2f}). {signal.reason}",
                {"order_id": result.order_id, "signal_id": signal.signal_id, "decision": decision.to_dict()},
            )
        else:
            self._audit(
                "PAPER_BUY_REJECTED",
                signal.symbol,
                f"Adapter rejected order: {result.message}",
                {"order_id": result.order_id},
            )
        return result

    # ------------------------------------------------------------------ #
    # Sell / trim flow (manual-review driven; never auto-forced)
    # ------------------------------------------------------------------ #
    def process_sell(
        self, symbol: str, quantity: int, price: float, reason: str
    ) -> Optional[OrderResult]:
        portfolio = storage.load_state("portfolio", {})
        decision = self.risk.evaluate_sell(symbol, quantity, portfolio, is_paper=self.adapter.is_paper)
        if not decision.approved:
            self._audit("SELL_REJECTED", symbol, decision.reason, {"decision": decision.to_dict()})
            return None
        req = OrderRequest(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            amount=round(quantity * price, 2),
            limit_price=round(price, 2),
            reason=reason,
            is_paper=self.adapter.is_paper,
        )
        result = self.adapter.place_order(req)
        if result.status == OrderState.FILLED:
            realized = next(
                (t.get("realized_pnl", 0.0) for t in reversed(storage.load_state("trade_history", []))
                 if t.get("order_id") == result.order_id),
                0.0,
            )
            self.pm.record_sell(realized)
            self._audit("PAPER_SELL_FILLED", symbol, f"Sold {quantity} @ ₹{price:.2f}. {reason}",
                        {"order_id": result.order_id, "realized_pnl": realized})
        return result

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _requires_approval(self) -> bool:
        # Paper orders auto-execute (that is how we collect a month of data).
        # Real orders would require manual approval — and are blocked in v1.
        return (not self.adapter.is_paper) and self.require_manual_approval

    def _queue_approval(self, req: OrderRequest, signal: TradeSignal) -> None:
        approvals = storage.load_state("approvals", [])
        if not isinstance(approvals, list):
            approvals = []
        approvals.append(
            {
                "approval_id": gen_id("apr"),
                "order_id": req.order_id,
                "symbol": req.symbol,
                "status": "PENDING",
                "requested_at": now_ist_iso(),
                "amount": req.amount,
                "reason": req.reason,
            }
        )
        storage.save_state("approvals", approvals)

    def _audit(self, event: str, symbol: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        record = {
            "event": event,
            "symbol": symbol,
            "message": message,
            "mode": self.exec_cfg.get("mode", "paper"),
            "broker_adapter": self.adapter.name,
            "is_paper": self.adapter.is_paper,
        }
        if extra:
            record.update(extra)
        storage.append_audit(record)

    def _audit_no_trade(self, signal: TradeSignal, message: str) -> None:
        self._audit("NO_TRADE", signal.symbol, message, {"signal_id": signal.signal_id, "score": signal.score})

    def _audit_rejected(self, signal: TradeSignal, decision: RiskDecision, amount, qty, price) -> None:
        self._audit(
            "BUY_REJECTED_RISK",
            signal.symbol,
            decision.reason,
            {
                "signal_id": signal.signal_id,
                "score": signal.score,
                "amount": amount,
                "quantity": qty,
                "price": price,
                "rules_failed": decision.rules_failed,
            },
        )
