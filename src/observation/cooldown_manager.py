"""CooldownManager — stop the observer from spamming the same alert/action.

Backed by data/state/alert_cooldowns.json. Tracks the last time we alerted on a
given (symbol, trigger) and the last paper-buy time per symbol, so a noisy market
can't produce duplicate emails or rapid-fire paper trades.
"""
from __future__ import annotations

from typing import Any, Dict

import storage
from utils import minutes_since, now_ist_iso, write_json

_FILE = "alert_cooldowns.json"


class CooldownManager:
    def __init__(self, cfg: Dict[str, Any]) -> None:
        cd = (cfg or {}).get("cooldowns", {})
        self.enabled = bool(cd.get("enabled", True))
        self.symbol_alert_min = float(cd.get("same_symbol_alert_cooldown_minutes", 120))
        self.trigger_alert_min = float(cd.get("same_trigger_alert_cooldown_minutes", 180))
        self.paper_trade_hours = float(cd.get("paper_trade_cooldown_after_buy_hours", 24))
        self.expiry_hours = float(cd.get("escalation_expiry_hours", 24))
        self.path = storage.state_file(_FILE)
        data = storage.read_json(self.path, {})
        self.data: Dict[str, Any] = data if isinstance(data, dict) else {}
        for k in ("symbol_alert", "trigger_alert", "paper_buy"):
            self.data.setdefault(k, {})

    # ------------------------------------------------------------------ #
    def _age_min(self, ts: Any) -> float:
        if not ts:
            return 1e9
        m = minutes_since(ts)
        return m if m is not None else 1e9

    def trigger_on_cooldown(self, symbol: str, trigger_type: str) -> bool:
        if not self.enabled:
            return False
        key = f"{symbol}:{trigger_type}"
        return self._age_min(self.data["trigger_alert"].get(key)) < self.trigger_alert_min

    def symbol_on_cooldown(self, symbol: str) -> bool:
        if not self.enabled:
            return False
        return self._age_min(self.data["symbol_alert"].get(symbol)) < self.symbol_alert_min

    def paper_buy_on_cooldown(self, symbol: str) -> bool:
        if not self.enabled:
            return False
        return self._age_min(self.data["paper_buy"].get(symbol)) < self.paper_trade_hours * 60.0

    # ------------------------------------------------------------------ #
    def stamp_alert(self, symbol: str, trigger_type: str) -> None:
        now = now_ist_iso()
        self.data["symbol_alert"][symbol] = now
        self.data["trigger_alert"][f"{symbol}:{trigger_type}"] = now

    def stamp_paper_buy(self, symbol: str) -> None:
        self.data["paper_buy"][symbol] = now_ist_iso()

    def save(self) -> None:
        write_json(self.path, self.data)
