"""Rebuild open paper positions from filled trades.

The portfolio snapshot can diverge from trade_history (duplicate JSON keys
dropped the 14 Oct buys). Filled trades are the source of truth for quantity
and cash. This is a no-op when the snapshot already matches net fills.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import storage
from utils import now_ist_iso


def reconcile_portfolio_from_trades() -> Optional[str]:
    trades = storage.load_state("trade_history", [])
    portfolio = storage.load_state("portfolio", {})
    if not isinstance(trades, list) or not isinstance(portfolio, dict) or not portfolio:
        return None

    filled = [t for t in trades if str(t.get("status", "")).upper() == "FILLED"]
    filled.sort(key=lambda t: str(t.get("timestamp") or ""))
    books: Dict[str, Dict[str, Any]] = {}
    closed: List[Dict[str, Any]] = []
    buy_notional = 0.0
    sell_notional = 0.0
    realized = 0.0

    for trade in filled:
        symbol = trade.get("symbol")
        if not symbol:
            continue
        qty = int(trade.get("quantity") or 0)
        price = float(trade.get("price") or 0.0)
        if qty < 1 or price <= 0:
            continue
        side = str(trade.get("side", "")).upper()
        book = books.setdefault(symbol, {"qty": 0, "cost": 0.0, "opened_at": trade.get("timestamp"), "exchange": trade.get("exchange") or "NSE"})
        if side == "BUY":
            book["qty"] += qty
            book["cost"] += qty * price
            buy_notional += qty * price
        elif side == "SELL" and book["qty"] > 0:
            sell_qty = min(qty, book["qty"])
            avg = book["cost"] / book["qty"]
            pnl = (price - avg) * sell_qty
            realized += pnl
            sell_notional += sell_qty * price
            closed.append({
                "symbol": symbol,
                "exchange": book["exchange"],
                "quantity": sell_qty,
                "avg_price": round(avg, 4),
                "exit_price": round(price, 4),
                "realized_pnl": round(pnl, 2),
                "realized_pnl_pct": round((price / avg - 1) * 100, 2) if avg else 0.0,
                "opened_at": book["opened_at"],
                "closed_at": trade.get("timestamp") or now_ist_iso(),
                "bot_owned": True,
                "reason": trade.get("reason") or "Rebuilt from filled trades.",
            })
            book["qty"] -= sell_qty
            book["cost"] -= avg * sell_qty

    expected = {sym for sym, book in books.items() if book["qty"] > 0}
    actual = {p.get("symbol") for p in portfolio.get("positions", []) if int(p.get("quantity") or 0) > 0}
    if expected == actual:
        return None

    starting = float(portfolio.get("starting_capital") or 10000.0)
    positions = []
    for symbol, book in books.items():
        if book["qty"] <= 0:
            continue
        avg = book["cost"] / book["qty"]
        positions.append({
            "symbol": symbol,
            "exchange": book["exchange"],
            "name": symbol,
            "quantity": book["qty"],
            "avg_price": round(avg, 4),
            "invested": round(book["cost"], 2),
            "last_price": round(avg, 4),
            "current_value": round(book["cost"], 2),
            "unrealized_pnl": 0.0,
            "unrealized_pnl_pct": 0.0,
            "bot_owned": True,
            "opened_at": book["opened_at"] or now_ist_iso(),
            "risk_status": "OK",
            "data_status": "OK",
        })

    portfolio["positions"] = positions
    portfolio["closed_positions"] = closed
    portfolio["cash"] = round(starting - buy_notional + sell_notional, 2)
    portfolio["realized_pnl"] = round(realized, 2)
    portfolio["as_of"] = now_ist_iso()
    storage.save_state("portfolio", portfolio)
    storage.append_audit({
        "event": "LEDGER_RECONCILED",
        "message": f"Rebuilt positions from fills. Open: {sorted(expected)}.",
    })
    return ", ".join(sorted(expected))
