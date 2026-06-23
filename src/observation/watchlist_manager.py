"""WatchlistManager — build the small ACTIVE watchlist the observer monitors.

In lightweight mode we do NOT scan the whole universe. We watch only what matters
right now:
  * open bot positions               (highest priority)
  * news-blocked / high-score buy candidates (high)
  * recent WATCH signals             (high/medium)
  * high-score rejections improving  (medium)
  * shadow candidates (declined but moving)  (low)
  * manually pinned names from universe.yml  (high)

Deduped by symbol (best priority wins), capped to max_active_symbols. Persisted
to data/state/active_watchlist.json.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import storage
from utils import now_ist_iso, today_ist_str, write_json

_FILE = "active_watchlist.json"

PRIORITY_RANK = {"HIGHEST": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}


class WatchlistManager:
    def __init__(self, configs: Dict[str, Any]) -> None:
        obs = (configs.get("observation") or {}).get("observation", {})
        wl = obs.get("watchlist", {})
        self.max_active = int(wl.get("max_active_symbols", 15))
        self.include_positions = bool(wl.get("include_open_positions", True))
        self.include_watch = bool(wl.get("include_recent_watch_signals", True))
        self.include_rejections = bool(wl.get("include_high_score_rejections", True))
        self.include_news_blocked = bool(wl.get("include_news_blocked_candidates", True))
        self.include_shadow = bool(wl.get("include_shadow_candidates", True))
        self.max_age_days = int(wl.get("max_age_days", 5))
        self.rejection_min = float(wl.get("high_score_rejection_min", 70))
        self.pinned = (configs.get("universe") or {}).get("watchlist_pinned", []) or []
        self.path = storage.state_file(_FILE)

    # ------------------------------------------------------------------ #
    def build(self) -> List[Dict[str, Any]]:
        items: Dict[str, Dict[str, Any]] = {}

        def add(symbol, name, exchange, source, reason, priority,
                score=None, label=None, last_price=None, is_open=False, is_bot=False):
            if not symbol:
                return
            cand = {
                "symbol": symbol, "name": name or symbol, "exchange": exchange or "NSE",
                "source": source, "reason_added": reason, "priority": priority,
                "score_when_added": score, "last_signal_label": label, "last_price": last_price,
                "trigger_levels": {}, "added_at": now_ist_iso(), "expires_at": None,
                "is_open_position": is_open, "is_bot_owned": is_bot,
            }
            cur = items.get(symbol)
            if cur is None or PRIORITY_RANK.get(priority, 0) > PRIORITY_RANK.get(cur["priority"], 0):
                items[symbol] = cand

        portfolio = storage.load_state("portfolio", {})
        # 1) open positions (highest).
        if self.include_positions:
            for p in portfolio.get("positions", []):
                add(p.get("symbol"), p.get("name"), p.get("exchange", "NSE"), "open_position",
                    "Open bot-owned position", "HIGHEST", last_price=p.get("last_price"),
                    is_open=True, is_bot=bool(p.get("bot_owned", True)))

        # 2) most-recent signal per symbol (recent only).
        latest = self._latest_signals_by_symbol()
        for sym, sig in latest.items():
            label = sig.get("label")
            score = float(sig.get("score", 0))
            name, exch, price = sig.get("name"), sig.get("exchange", "NSE"), sig.get("last_price")
            if self.include_news_blocked and sig.get("news_blocks_buy"):
                add(sym, name, exch, "news_blocked", "Buy candidate blocked by news", "HIGH",
                    score, label, price)
            elif self.include_watch and label == "WATCH":
                add(sym, name, exch, "watch_signal", "Recent WATCH signal", "HIGH", score, label, price)
            elif self.include_rejections and score >= self.rejection_min and label in (
                    "NO_ACTION", "DO_NOT_BUY", "MANUAL_REVIEW"):
                add(sym, name, exch, "high_score_rejection", "High score but not bought (improving?)",
                    "MEDIUM", score, label, price)

        # 3) shadow candidates (declined but moving) from the Decision Quality Engine.
        if self.include_shadow:
            dq = storage.read_json(storage.report_file("decision_quality.json"), {})
            for ep in (dq.get("shadow", {}) or {}).get("shadow_examples", [])[:10]:
                add(ep.get("symbol"), ep.get("name"), "NSE", "shadow_candidate",
                    f"Shadow candidate (fwd {ep.get('forward_return_pct')}%)", "LOW",
                    ep.get("score"), ep.get("label_at_open"), ep.get("last_price"))

        # 4) manually pinned names.
        for pin in self.pinned:
            sym = (pin.get("symbol") if isinstance(pin, dict) else str(pin)).strip().upper()
            add(sym, pin.get("name") if isinstance(pin, dict) else sym, "NSE", "pinned",
                "Manually pinned", "HIGH")

        # Stamp expiry + rank, cap to max_active by priority then recency.
        out = list(items.values())
        for it in out:
            it["expires_at"] = today_ist_str()  # informational; refreshed each build
        out.sort(key=lambda it: PRIORITY_RANK.get(it["priority"], 0), reverse=True)
        out = out[: self.max_active]
        return out

    def build_and_save(self) -> List[Dict[str, Any]]:
        wl = self.build()
        write_json(self.path, wl)
        return wl

    def current(self) -> List[Dict[str, Any]]:
        wl = storage.read_json(self.path, [])
        return wl if isinstance(wl, list) else []

    # ------------------------------------------------------------------ #
    def _latest_signals_by_symbol(self) -> Dict[str, Dict[str, Any]]:
        history = storage.load_state("signal_history", [])
        if not isinstance(history, list):
            return {}
        latest: Dict[str, Dict[str, Any]] = {}
        for sig in history:  # chronological; later entries overwrite
            sym = sig.get("symbol")
            if sym:
                latest[sym] = sig
        return latest
