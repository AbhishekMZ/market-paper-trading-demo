"""Forward-return tracker — the spine of decision-quality measurement.

Problem it solves: a score is only meaningful if high-scoring signals actually
go up afterwards. We can't know that at signal time, so we TRACK each symbol
forward across subsequent runs and record the realized price path.

Model: one OPEN "episode" per symbol. When a priced signal arrives and the
symbol has no open episode, we open one (snapshotting the signal's score, label,
contributors, news/DQ flags, and whether it was acted on). Each later run we
re-price the open episode and update its forward return. After `maturity_runs`
updates the episode is archived and a fresh one may open.

Pure persistence + arithmetic. No look-ahead: every update uses only the price
available on that run. Ledger: data/state/forward_returns.json.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import storage
from utils import now_ist_iso, today_ist_str, write_json

_LEDGER = "forward_returns.json"


class ForwardReturnTracker:
    def __init__(self, cfg: Dict[str, Any]) -> None:
        fr = (cfg or {}).get("forward_returns", {})
        self.maturity_runs = int(fr.get("maturity_runs", 5))
        self.max_archived = int(fr.get("max_archived_per_symbol", 10))
        self.open_min_score = float(fr.get("open_min_score", 0))
        self.score_bands = fr.get("score_bands", [[80, 201, "buy_grade"], [65, 80, "watch_grade"], [0, 65, "low_grade"]])
        self.path = storage.state_file(_LEDGER)
        led = storage.read_json(self.path, {})
        self.ledger: Dict[str, Any] = led if isinstance(led, dict) else {}
        self.ledger.setdefault("open", {})       # symbol -> episode
        self.ledger.setdefault("archived", [])   # list of matured episodes

    # ------------------------------------------------------------------ #
    def update(self, signals: List[Dict[str, Any]], prices: Dict[str, Optional[float]]) -> None:
        """Open new episodes and advance/mature existing ones for this run."""
        today = today_ist_str()
        for sig in signals:
            sym = sig.get("symbol")
            price = prices.get(sym) or sig.get("last_price")
            if not sym or not price or price <= 0:
                continue
            price = float(price)
            ep = self.ledger["open"].get(sym)
            if ep is None:
                if float(sig.get("score", 0)) >= self.open_min_score:
                    self.ledger["open"][sym] = self._open_episode(sig, price, today)
                continue
            self._advance(ep, price, today)
            if ep["runs_tracked"] >= self.maturity_runs:
                ep["status"] = "MATURED"
                self.ledger["archived"].append(ep)
                del self.ledger["open"][sym]
        # Bound archived history per symbol.
        self._bound_archived()

    def save(self) -> None:
        write_json(self.path, self.ledger)

    # ------------------------------------------------------------------ #
    def episodes(self) -> List[Dict[str, Any]]:
        """All episodes (open + archived) for downstream analysis."""
        return list(self.ledger["open"].values()) + list(self.ledger["archived"])

    def summary(self) -> Dict[str, Any]:
        eps = self.episodes()
        matured = [e for e in eps if e.get("status") == "MATURED"]
        by_band = {}
        for low, high, label in self.score_bands:
            band_eps = [e for e in eps if low <= e.get("score", 0) < high]
            by_band[label] = self._stat(band_eps)
        return {
            "as_of": now_ist_iso(),
            "open_episodes": len(self.ledger["open"]),
            "matured_episodes": len(matured),
            "total_episodes": len(eps),
            "by_score_band": by_band,
            "acted": self._stat([e for e in eps if e.get("acted")]),
            "not_acted": self._stat([e for e in eps if not e.get("acted")]),
        }

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _open_episode(self, sig: Dict[str, Any], price: float, today: str) -> Dict[str, Any]:
        contributors = [r.get("strategy_name") for r in sig.get("strategy_results", [])
                        if r.get("contributes_to_score")]
        return {
            "symbol": sig.get("symbol"),
            "name": sig.get("name"),
            "signal_id": sig.get("signal_id"),
            "label_at_open": sig.get("label"),
            "score": float(sig.get("score", 0)),
            "checkpoint": sig.get("checkpoint"),
            "contributors": contributors,
            "news_risk_level": sig.get("news_risk_level", "NONE"),
            "news_blocked": bool(sig.get("news_blocks_buy")),
            "data_quality_verdict": sig.get("data_quality_verdict", "OK"),
            "acted": bool(sig.get("led_to_paper_trade")),
            "entry_date": today,
            "entry_price": round(price, 4),
            "last_price": round(price, 4),
            "last_update": today,
            "runs_tracked": 0,
            "forward_return_pct": 0.0,
            "max_return_pct": 0.0,
            "min_return_pct": 0.0,
            "status": "OPEN",
        }

    def _advance(self, ep: Dict[str, Any], price: float, today: str) -> None:
        entry = float(ep["entry_price"]) or price
        ret = round((price / entry - 1) * 100, 2) if entry else 0.0
        ep["last_price"] = round(price, 4)
        ep["last_update"] = today
        ep["runs_tracked"] = int(ep.get("runs_tracked", 0)) + 1
        ep["forward_return_pct"] = ret
        ep["max_return_pct"] = round(max(float(ep.get("max_return_pct", 0.0)), ret), 2)
        ep["min_return_pct"] = round(min(float(ep.get("min_return_pct", 0.0)), ret), 2)

    def _bound_archived(self) -> None:
        per_symbol: Dict[str, List[Dict[str, Any]]] = {}
        for e in self.ledger["archived"]:
            per_symbol.setdefault(e.get("symbol"), []).append(e)
        kept: List[Dict[str, Any]] = []
        for _sym, eps in per_symbol.items():
            kept.extend(eps[-self.max_archived:])
        self.ledger["archived"] = kept

    @staticmethod
    def _stat(eps: List[Dict[str, Any]]) -> Dict[str, Any]:
        rets = [float(e.get("forward_return_pct", 0.0)) for e in eps if e.get("runs_tracked", 0) > 0]
        n = len(rets)
        if n == 0:
            return {"count": len(eps), "rated": 0, "avg_return_pct": 0.0, "hit_rate_pct": 0.0}
        wins = sum(1 for r in rets if r > 0)
        return {
            "count": len(eps),
            "rated": n,
            "avg_return_pct": round(sum(rets) / n, 2),
            "hit_rate_pct": round(wins / n * 100, 1),
        }
