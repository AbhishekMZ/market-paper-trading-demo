"""ObservationState — what each watched symbol looked like last time.

Lightweight per-symbol memory (last price, last regime, last news risk, last
data-quality verdict) so the trigger rules can detect *changes* between runs.
Backed by data/state/observation_state.json.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import storage
from utils import now_ist_iso, write_json

_FILE = "observation_state.json"


class ObservationState:
    def __init__(self) -> None:
        self.path = storage.state_file(_FILE)
        data = storage.read_json(self.path, {})
        self.data: Dict[str, Any] = data if isinstance(data, dict) else {}
        self.data.setdefault("symbols", {})
        self.data.setdefault("last_observation_at", None)
        self.data.setdefault("last_regime", None)

    def get(self, symbol: str) -> Dict[str, Any]:
        return self.data["symbols"].get(symbol, {})

    def set(self, symbol: str, snapshot: Dict[str, Any]) -> None:
        self.data["symbols"][symbol] = {**snapshot, "updated_at": now_ist_iso()}

    @property
    def last_regime(self) -> Optional[str]:
        return self.data.get("last_regime")

    @last_regime.setter
    def last_regime(self, value: Optional[str]) -> None:
        self.data["last_regime"] = value

    def mark_observation(self, regime: Optional[str]) -> None:
        self.data["last_observation_at"] = now_ist_iso()
        if regime:
            self.data["last_regime"] = regime

    def save(self) -> None:
        write_json(self.path, self.data)
