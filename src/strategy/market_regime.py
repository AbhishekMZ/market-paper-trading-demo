"""MarketRegimeEngine — classify the overall market context.

Regimes: RISK_ON, NEUTRAL, RISK_OFF, EVENT_RISK, DATA_INSUFFICIENT.

RISK_ON / RISK_OFF / NEUTRAL come from the index's trailing 20-session return
(the same benchmark series the historical-context engine fetches). A one-day
spike sets `event_spike` and asks for manual review; it does not also set the
regime score. With no multi-day return, the label stays NEUTRAL (or
DATA_INSUFFICIENT if there is no benchmark at all) so a noisy day is not both
a score and a hard gate.

It NEVER fabricates index data; with no benchmark data it returns
DATA_INSUFFICIENT, which blocks new buys by default.
"""
from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional

from strategy.base import map_linear
from utils import now_ist_iso

RISK_ON = "RISK_ON"
NEUTRAL = "NEUTRAL"
RISK_OFF = "RISK_OFF"
EVENT_RISK = "EVENT_RISK"
DATA_INSUFFICIENT = "DATA_INSUFFICIENT"


@dataclass
class RegimeResult:
    regime: str
    score: float                 # 0-100 component for the hybrid engine
    confidence: float
    reason: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    blocks_new_buys: bool = False
    timestamp: str = field(default_factory=now_ist_iso)
    event_spike: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketRegimeEngine:
    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        cfg = cfg or {}
        self.risk_on_20d = float(cfg.get("risk_on_20d_pct", 5.0))
        self.risk_off_20d = float(cfg.get("risk_off_20d_pct", -5.0))
        self.event_move_pct = float(cfg.get("event_move_pct", 2.5))

    def classify(self, benchmarks: Dict[str, Dict[str, Any]], trailing: Optional[Dict[str, Any]] = None) -> RegimeResult:
        usable = {k: v for k, v in (benchmarks or {}).items() if v and v.get("ok")}
        changes = [v.get("change_pct") for v in usable.values() if v.get("change_pct") is not None]
        avg_change = statistics.fmean(changes) if changes else None
        max_abs_move = max((abs(c) for c in changes), default=0.0)
        event_spike = bool(usable) and max_abs_move >= self.event_move_pct

        ret20 = None
        if isinstance(trailing, dict) and trailing.get("return_20d_pct") is not None:
            try:
                ret20 = float(trailing["return_20d_pct"])
            except (TypeError, ValueError):
                ret20 = None

        inputs = {
            "benchmarks": {k: v.get("change_pct") for k, v in usable.items()},
            "avg_change_pct": round(avg_change, 3) if avg_change is not None else None,
            "return_20d_pct": None if ret20 is None else round(ret20, 3),
            "max_abs_move_pct": round(max_abs_move, 3),
            "event_spike": event_spike,
        }

        if not usable and ret20 is None:
            return RegimeResult(
                regime=DATA_INSUFFICIENT,
                score=50.0,
                confidence=0.1,
                reason="No benchmark index data available; new buys blocked by default.",
                inputs={"available_benchmarks": list((benchmarks or {}).keys())},
                blocks_new_buys=True,
            )

        if ret20 is None:
            result = RegimeResult(
                regime=NEUTRAL,
                score=55.0,
                confidence=0.35,
                reason="Multi-day index return unavailable; the one-day move is an event flag only.",
                inputs=inputs,
                blocks_new_buys=False,
                event_spike=event_spike,
            )
        elif ret20 >= self.risk_on_20d:
            score = max(65.0, map_linear(ret20, 0.0, 10.0, default=70.0))
            result = RegimeResult(
                RISK_ON, score, 0.7,
                f"Index {ret20:+.2f}% over 20 sessions — risk-on.",
                inputs, blocks_new_buys=False, event_spike=event_spike,
            )
        elif ret20 <= self.risk_off_20d:
            score = min(35.0, map_linear(ret20, -10.0, 0.0, default=30.0))
            result = RegimeResult(
                RISK_OFF, score, 0.7,
                f"Index {ret20:+.2f}% over 20 sessions — risk-off. New buys blocked.",
                inputs, blocks_new_buys=True, event_spike=event_spike,
            )
        else:
            result = RegimeResult(
                NEUTRAL, 55.0, 0.55,
                f"Index {ret20:+.2f}% over 20 sessions — neutral regime.",
                inputs, blocks_new_buys=False, event_spike=event_spike,
            )

        if event_spike:
            result.reason += (
                f" One-day move {max_abs_move:.2f}% flagged for manual review "
                "(does not set the regime score)."
            )
        return result
