"""MarketRegimeEngine — classify the overall market context.

Regimes: RISK_ON, NEUTRAL, RISK_OFF, EVENT_RISK, DATA_INSUFFICIENT.

It reads benchmark index data (NIFTY 50 and, if available, NIFTY Bank) from
SerpApi and produces both a regime label (used to GATE new buys) and a 0-100
regime score (used as a weighted component in the hybrid score).

It NEVER fabricates index data; with no benchmark data it returns
DATA_INSUFFICIENT, which blocks new buys by default.
"""
from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketRegimeEngine:
    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        cfg = cfg or {}
        self.risk_on_pct = float(cfg.get("risk_on_change_pct", 0.6))
        self.risk_off_pct = float(cfg.get("risk_off_change_pct", -0.75))
        self.event_move_pct = float(cfg.get("event_move_pct", 2.5))
        self.high_vol_pct = float(cfg.get("high_vol_pct", 1.5))

    def classify(self, benchmarks: Dict[str, Dict[str, Any]]) -> RegimeResult:
        usable = {k: v for k, v in (benchmarks or {}).items() if v and v.get("ok")}
        if not usable:
            return RegimeResult(
                regime=DATA_INSUFFICIENT,
                score=50.0,
                confidence=0.1,
                reason="No benchmark index data available; new buys blocked by default.",
                inputs={"available_benchmarks": list((benchmarks or {}).keys())},
                blocks_new_buys=True,
            )

        changes = [v.get("change_pct") for v in usable.values() if v.get("change_pct") is not None]
        avg_change = statistics.fmean(changes) if changes else None

        # Volatility proxy from the primary index graph (first usable benchmark).
        primary = next(iter(usable.values()))
        vol_pct = self._volatility(primary)
        max_abs_move = max((abs(c) for c in changes), default=0.0)

        inputs = {
            "benchmarks": {k: v.get("change_pct") for k, v in usable.items()},
            "avg_change_pct": round(avg_change, 3) if avg_change is not None else None,
            "index_volatility_pct": round(vol_pct, 3) if vol_pct is not None else None,
            "max_abs_move_pct": round(max_abs_move, 3),
        }

        # Event risk: an extreme index move or very high intraday volatility.
        if max_abs_move >= self.event_move_pct or (vol_pct is not None and vol_pct >= self.high_vol_pct):
            return RegimeResult(
                regime=EVENT_RISK,
                score=32.0,
                confidence=0.6,
                reason=(
                    f"Index moved {max_abs_move:.2f}% / volatility {vol_pct or 0:.2f}% — elevated event risk. "
                    "New buys require manual review."
                ),
                inputs=inputs,
                blocks_new_buys=False,  # downgraded to MANUAL_REVIEW by the hybrid engine
            )

        if avg_change is None:
            return RegimeResult(
                regime=DATA_INSUFFICIENT, score=50.0, confidence=0.2,
                reason="Benchmark change unavailable.", inputs=inputs, blocks_new_buys=True,
            )

        if avg_change >= self.risk_on_pct:
            score = map_linear(avg_change, 0.0, 2.0, default=70.0)
            return RegimeResult(RISK_ON, max(65.0, score), 0.7,
                                f"Benchmarks up {avg_change:.2f}% on average — risk-on.",
                                inputs, blocks_new_buys=False)
        if avg_change <= self.risk_off_pct:
            score = map_linear(avg_change, -2.0, 0.0, default=30.0)
            return RegimeResult(RISK_OFF, min(35.0, score), 0.7,
                                f"Benchmarks down {avg_change:.2f}% on average — risk-off. New buys blocked.",
                                inputs, blocks_new_buys=True)

        return RegimeResult(NEUTRAL, 55.0, 0.5,
                            f"Benchmarks roughly flat ({avg_change:.2f}%) — neutral regime.",
                            inputs, blocks_new_buys=False)

    @staticmethod
    def _volatility(market_data: Dict[str, Any]) -> Optional[float]:
        # Return-based volatility (detrended), consistent with VolatilityRiskStrategy.
        prices = [p["price"] for p in (market_data.get("graph") or []) if p.get("price") is not None]
        if len(prices) < 4:
            return None
        returns = [(b - a) / a for a, b in zip(prices, prices[1:]) if a]
        if len(returns) < 2:
            return None
        return statistics.pstdev(returns) * 100.0
