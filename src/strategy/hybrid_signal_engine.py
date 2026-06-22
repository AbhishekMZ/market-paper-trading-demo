"""HybridSignalEngine — combine strategy plugins into one explainable signal.

Pipeline per symbol:
  1. Run every enabled strategy plugin (errors are isolated, never fatal).
  2. Weight the contributing strategies + the market-regime score into a final
     0-100 score (weights from config/scoring.yml -> hybrid_scoring.weights).
  3. Subtract transparent risk penalties.
  4. Derive a label from thresholds, then apply REGIME GATING and CONFLICT
     handling (prefer NO_ACTION when strategies disagree).
  5. Attach per-strategy evidence, warnings, and an estimated round-trip cost.

v1 is deterministic, auditable, and boring by design: no ML, no self-tuning.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from order_models import DataQuality, RiskLevel, SignalLabel, TradeSignal
from strategy.base import NEGATIVE, POSITIVE, StrategyPlugin
from strategy.breakout import BreakoutStrategy
from strategy.market_regime import (
    DATA_INSUFFICIENT,
    EVENT_RISK,
    NEUTRAL as REGIME_NEUTRAL,
    RISK_OFF,
    RISK_ON,
    RegimeResult,
)
from strategy.mean_reversion import MeanReversionStrategy
from strategy.news_event_risk import NewsEventRiskStrategy
from strategy.portfolio_fit import PortfolioFitStrategy
from strategy.relative_strength import RelativeStrengthStrategy
from strategy.trend_following import TrendFollowingStrategy
from strategy.volatility_risk import VolatilityRiskStrategy
from utils import clamp, gen_id, minutes_since

# Plugin classes registered by name. market_regime is handled separately
# (it is an engine, not a per-symbol plugin) but still carries a weight.
PLUGIN_CLASSES = {
    "trend_following": TrendFollowingStrategy,
    "relative_strength": RelativeStrengthStrategy,
    "mean_reversion": MeanReversionStrategy,
    "breakout": BreakoutStrategy,
    "news_event_risk": NewsEventRiskStrategy,
    "volatility_risk": VolatilityRiskStrategy,
    "portfolio_fit": PortfolioFitStrategy,
}


class HybridSignalEngine:
    def __init__(self, configs: Dict[str, Any], cost_model: Any = None) -> None:
        scoring = configs["scoring"].get("hybrid_scoring", {})
        self.enabled = bool(scoring.get("enabled", True))
        self.weights: Dict[str, float] = dict(scoring.get("weights", {}))
        self.buy_threshold = float(scoring.get("buy_threshold", 80))
        self.watch_threshold = float(scoring.get("watch_threshold", 65))
        self.no_action_threshold = float(scoring.get("no_action_threshold", 50))
        self.do_not_buy_threshold = float(scoring.get("do_not_buy_threshold", 35))
        self.conflict_behavior = scoring.get("conflict_behavior", "prefer_no_action")
        self.risk_off_blocks = bool(scoring.get("risk_off_blocks_new_buys", True))
        self.data_insufficient_blocks = bool(scoring.get("data_insufficient_blocks_new_buys", True))
        self.experimental = scoring.get("experimental_strategies", {})
        self.penalties = configs["scoring"].get("scoring", {}).get("risk_penalties", {})
        self.data_quality_cfg = configs["settings"].get("data_quality", {})
        self.max_data_age = float(self.data_quality_cfg.get("max_data_age_minutes", 1440))
        self.cost_model = cost_model

        # Instantiate plugins and resolve which ones contribute to the score.
        self.plugins: Dict[str, StrategyPlugin] = {n: cls() for n, cls in PLUGIN_CLASSES.items()}
        self.contributes: Dict[str, bool] = {}
        for name in PLUGIN_CLASSES:
            weight = float(self.weights.get(name, 0))
            exp = self.experimental.get(name, {})
            allowed = exp.get("contributes_to_score", True)
            self.contributes[name] = weight > 0 and bool(allowed)
        # market_regime contributes if it has a positive weight.
        self.regime_contributes = float(self.weights.get("market_regime", 0)) > 0

    # ------------------------------------------------------------------ #
    # Main entry
    # ------------------------------------------------------------------ #
    def evaluate(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        context: Dict[str, Any],
        meta: Optional[Dict[str, str]] = None,
    ) -> TradeSignal:
        meta = meta or {}
        # Accept a normalized MarketSnapshot (from a MarketDataProvider) OR the
        # already-flattened dict. Strategies always receive the flat dict.
        if hasattr(market_data, "to_market_data"):
            market_data = market_data.to_market_data(name=meta.get("name"), exchange=meta.get("exchange"))
        regime: RegimeResult = context.get("regime")
        name = meta.get("name", market_data.get("name", symbol))
        exchange = meta.get("exchange", market_data.get("exchange", "NSE"))
        quality = self._assess_quality(market_data)

        # Run every plugin (display-only and contributing alike, for transparency).
        results = []
        for pname, plugin in self.plugins.items():
            res = plugin._safe_evaluate(symbol, market_data, portfolio_state, context)
            res.contributes_to_score = self.contributes.get(pname, False) and res.is_valid
            res.display_only = not self.contributes.get(pname, False)
            results.append(res)

        # ---- weighted combination (plugins + regime) -------------------- #
        weighted_sum = 0.0
        total_weight = 0.0
        for res in results:
            if not res.contributes_to_score:
                continue
            w = float(self.weights.get(res.strategy_name, 0))
            weighted_sum += res.score_contribution * w
            total_weight += w
        if regime is not None and self.regime_contributes:
            w = float(self.weights.get("market_regime", 0))
            weighted_sum += regime.score * w
            total_weight += w

        raw_score = (weighted_sum / total_weight) if total_weight else 50.0

        # ---- risk penalties (transparent, light, no double-counting) ---- #
        penalty, penalty_notes = self._risk_penalties(results, quality)
        final_score = round(clamp(raw_score - penalty, 0.0, 100.0), 1)

        # ---- conflict detection ---------------------------------------- #
        conflicts = self._detect_conflicts(results)

        # ---- base label from thresholds -------------------------------- #
        label = self._base_label(final_score, symbol, context.get("held_symbols", []))

        # ---- confidence ------------------------------------------------- #
        confidence = self._confidence(results, regime, quality)

        # ---- regime + conflict gating ---------------------------------- #
        label, gating_notes = self._apply_gating(label, regime, conflicts, confidence, quality)

        risk_level = self._risk_level(final_score, results, regime, quality)
        est_cost = self._estimate_cost(market_data, context)

        reason = self._reason(final_score, results, regime, label, penalty_notes, gating_notes, conflicts)
        warnings = sorted({w for r in results for w in r.warnings})
        if regime is not None and regime.regime in (RISK_OFF, EVENT_RISK, DATA_INSUFFICIENT):
            warnings.append(f"Market regime: {regime.regime}.")

        return TradeSignal(
            signal_id=gen_id("sig"),
            symbol=symbol,
            name=name,
            exchange=exchange,
            score=final_score,
            label=label,
            risk_level=risk_level,
            confidence=confidence,
            data_quality=quality,
            reason=reason,
            last_price=market_data.get("price"),
            checkpoint=context.get("checkpoint", ""),
            score_breakdown={r.strategy_name: r.score_contribution for r in results},
            market_regime=regime.regime if regime is not None else "UNKNOWN",
            strategy_results=[r.to_dict() for r in results],
            conflict_warnings=conflicts,
            warnings=warnings,
            estimated_cost=est_cost,
            data_snapshot={
                "price": market_data.get("price"),
                "change_pct": market_data.get("change_pct"),
                "graph_points": market_data.get("graph_points", 0),
                "extracted_at": market_data.get("extracted_at"),
                "headlines_count": len(market_data.get("headlines", []) or []),
            },
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _base_label(self, score: float, symbol: str, held: List[str]) -> SignalLabel:
        if score >= self.buy_threshold:
            return SignalLabel.BUY_SMALL_PAPER
        if score >= self.watch_threshold:
            return SignalLabel.WATCH
        if score >= self.no_action_threshold:
            return SignalLabel.HOLD if symbol in held else SignalLabel.NO_ACTION
        if score >= self.do_not_buy_threshold:
            return SignalLabel.DO_NOT_BUY
        return SignalLabel.HIGH_RISK_IGNORE

    def _apply_gating(self, label, regime, conflicts, confidence, quality):
        notes: List[str] = []
        is_buy = label == SignalLabel.BUY_SMALL_PAPER

        # Conflict handling.
        if conflicts and is_buy and self.conflict_behavior == "prefer_no_action":
            label = SignalLabel.WATCH
            is_buy = False
            notes.append("Strategy conflict -> downgraded to WATCH (prefer no action).")

        # Regime gating.
        if regime is not None:
            if regime.regime == RISK_OFF and self.risk_off_blocks and is_buy:
                label = SignalLabel.WATCH
                notes.append("RISK_OFF regime -> new buys blocked; downgraded to WATCH.")
            elif regime.regime == DATA_INSUFFICIENT and self.data_insufficient_blocks and is_buy:
                label = SignalLabel.NO_ACTION
                notes.append("DATA_INSUFFICIENT regime -> no new buys.")
            elif regime.regime == EVENT_RISK and is_buy:
                label = SignalLabel.MANUAL_REVIEW
                notes.append("EVENT_RISK regime -> requires manual review before any buy.")
            elif regime.regime == REGIME_NEUTRAL and is_buy and confidence < 0.55:
                label = SignalLabel.WATCH
                notes.append("NEUTRAL regime + modest confidence -> downgraded to WATCH.")

        # Weak data never becomes a buy.
        if label == SignalLabel.BUY_SMALL_PAPER and quality in (DataQuality.WEAK, DataQuality.MISSING):
            label = SignalLabel.NO_ACTION
            notes.append("Weak/missing data -> no buy.")
        return label, notes

    def _detect_conflicts(self, results) -> List[str]:
        strong_pos = [r.strategy_name for r in results if r.contributes_to_score and r.score_contribution >= 65 and r.signal == POSITIVE]
        strong_neg = [r.strategy_name for r in results if r.contributes_to_score and r.score_contribution <= 35 and r.signal == NEGATIVE]
        if strong_pos and strong_neg:
            return [f"Disagreement: {strong_pos} positive vs {strong_neg} negative."]
        return []

    def _risk_penalties(self, results, quality) -> tuple[float, List[str]]:
        total = 0.0
        notes: List[str] = []
        flags = {f for r in results for f in r.risk_flags}
        if quality == DataQuality.ACCEPTABLE:
            total += self.penalties.get("stale_data", 0) * 0.3
            notes.append("limited_data")
        if quality in (DataQuality.WEAK, DataQuality.MISSING):
            total += self.penalties.get("stale_data", 0) * 0.8
            notes.append("weak_data")
        if "extreme_daily_move" in flags:
            total += self.penalties.get("high_volatility", 0)
            notes.append("extreme_daily_move")
        return total, notes

    def _confidence(self, results, regime, quality) -> float:
        weighted, tw = 0.0, 0.0
        for r in results:
            if not r.contributes_to_score:
                continue
            w = float(self.weights.get(r.strategy_name, 0))
            weighted += r.confidence * w
            tw += w
        base = (weighted / tw) if tw else 0.3
        if regime is not None:
            base = 0.85 * base + 0.15 * regime.confidence
        q_factor = {DataQuality.GOOD: 1.0, DataQuality.ACCEPTABLE: 0.8, DataQuality.WEAK: 0.4, DataQuality.MISSING: 0.1}[quality]
        return round(clamp(base * q_factor, 0.0, 0.95), 2)

    def _risk_level(self, score, results, regime, quality) -> RiskLevel:
        flags = {f for r in results for f in r.risk_flags}
        if quality in (DataQuality.WEAK, DataQuality.MISSING):
            return RiskLevel.HIGH
        if regime is not None and regime.regime in (RISK_OFF, EVENT_RISK):
            return RiskLevel.HIGH
        if "extreme_daily_move" in flags or score < self.no_action_threshold:
            return RiskLevel.HIGH
        if "large_daily_move" in flags or quality == DataQuality.ACCEPTABLE or score < self.watch_threshold:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _estimate_cost(self, market_data, context) -> float:
        if not self.cost_model:
            return 0.0
        price = market_data.get("price")
        max_trade = float(context.get("limits", {}).get("max_trade_amount", 2000))
        if not price or price <= 0:
            return 0.0
        qty = int(max_trade // price)
        if qty < 1:
            return 0.0
        amount = qty * price
        try:
            return round(self.cost_model.round_trip_cost(amount), 2)
        except Exception:
            return 0.0

    def _assess_quality(self, m: Dict[str, Any]) -> DataQuality:
        if not m.get("ok") or m.get("price") is None:
            return DataQuality.MISSING
        age = minutes_since(m.get("extracted_at"))
        if age is not None and age > self.max_data_age:
            return DataQuality.WEAK
        fields = sum(1 for k in ("price", "change_pct", "previous_close") if m.get(k) is not None)
        pts = m.get("graph_points", 0)
        if fields >= 3 and pts >= 5:
            return DataQuality.GOOD
        if m.get("price") is not None and (fields >= 2 or pts >= 1):
            return DataQuality.ACCEPTABLE
        return DataQuality.WEAK

    def _reason(self, score, results, regime, label, penalty_notes, gating_notes, conflicts) -> str:
        contributing = [(r.strategy_name, r.score_contribution) for r in results if r.contributes_to_score]
        top = sorted(contributing, key=lambda kv: kv[1], reverse=True)[:3]
        top_txt = ", ".join(f"{n}={v:.0f}" for n, v in top) if top else "n/a"
        regime_txt = f"{regime.regime}" if regime is not None else "UNKNOWN"
        parts = [f"Final {score:.1f}/100 -> {label.value} [regime {regime_txt}]. Top: {top_txt}."]
        if penalty_notes:
            parts.append(f"Penalties: {', '.join(penalty_notes)}.")
        if conflicts:
            parts.append(conflicts[0])
        if gating_notes:
            parts.append(" ".join(gating_notes))
        return " ".join(parts)
