"""HistoricalContextOverlay — caution-only application of trailing context.

Cardinal rules (enforced, not just documented):
  * Acts ONLY on a BUY_SMALL_PAPER label. A 'downgrade' rule sets it to WATCH.
  * NEVER creates or upgrades a label. NEVER reads or writes signal.score.
  * Missing/insufficient features -> no-op (sets hist_context_available=False).
  * Exception-safe; degrades to "no context".
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from order_models import SignalLabel


class HistoricalContextOverlay:
    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        cfg = cfg or {}
        self.enabled = bool(cfg.get("enabled", True))
        caution = cfg.get("caution", {})
        self.caution = caution if isinstance(caution, dict) else {}

    # ------------------------------------------------------------------ #
    def _rule(self, name: str) -> Dict[str, Any]:
        r = self.caution.get(name, {})
        return r if isinstance(r, dict) else {}

    def evaluate(self, features: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Pure: decide which caution rules fire. Returns flags/downgrade/reasons."""
        result: Dict[str, Any] = {"flags": [], "downgrade": False, "reasons": []}
        if not self.enabled or not features or features.get("coverage") != "ok":
            return result

        def fire(name: str, reason: str) -> None:
            action = str(self._rule(name).get("action", "flag")).lower()
            result["flags"].append(name)
            result["reasons"].append(reason)
            if action == "downgrade":
                result["downgrade"] = True

        volp = features.get("vol_percentile")
        ev = self._rule("elevated_volatility")
        if ev.get("enabled", True) and volp is not None and volp >= float(ev.get("vol_percentile_gte", 90)):
            fire("elevated_volatility", f"volatility in the {volp:.0f}th percentile of 2y")

        turn = features.get("avg_turnover_20d")
        tl = self._rule("thin_liquidity")
        if tl.get("enabled", True) and turn is not None and turn < float(tl.get("min_avg_turnover", 50000000)):
            fire("thin_liquidity", f"thin liquidity (avg turnover {turn:,.0f})")

        above = features.get("pct_above_200dma")
        rangep = features.get("range_position_2y")
        oe = self._rule("overextended")
        if (oe.get("enabled", True) and above is not None and rangep is not None
                and above >= float(oe.get("pct_above_200dma_gte", 15))
                and rangep >= float(oe.get("range_position_gte", 0.95))):
            fire("overextended", f"price {above:.0f}% above 200-DMA and near 2y high")

        dd = features.get("current_drawdown")
        do = self._rule("deep_drawdown")
        if do.get("enabled", False) and dd is not None and dd <= float(do.get("current_drawdown_lte", -25)):
            fire("deep_drawdown", f"deep drawdown {dd:.0f}% from 2y peak")

        return result

    # ------------------------------------------------------------------ #
    def apply_to_signal(self, signal, features: Optional[Dict[str, Any]]) -> None:
        try:
            self._apply(signal, features)
        except Exception:
            signal.hist_context_available = False  # never break the run

    def _apply(self, signal, features: Optional[Dict[str, Any]]) -> None:
        available = bool(features) and features.get("coverage") == "ok"
        signal.hist_context_available = available
        if available:
            signal.hist_vol_percentile = features.get("vol_percentile")
            signal.hist_range_position = features.get("range_position_2y")
            signal.hist_pct_above_200dma = features.get("pct_above_200dma")
            signal.hist_beta = features.get("beta_vs_nifty")

        decision = self.evaluate(features)
        signal.hist_context_flags = list(decision["flags"])
        signal.hist_context_note = "; ".join(decision["reasons"])

        # Caution-only: only ever downgrade a BUY. Never upgrade, never touch score.
        if signal.label == SignalLabel.BUY_SMALL_PAPER and decision["downgrade"]:
            signal.label = SignalLabel.WATCH
            note = "; ".join(decision["reasons"]) or "elevated historical risk"
            signal.warnings = list(signal.warnings) + [
                f"HistContext: {note} -> buy downgraded to WATCH."
            ]
            signal.reason = "[CONTEXT] " + signal.reason
