"""TriggerRules — deterministic, explainable change detection.

Given a fresh lightweight snapshot for a watched symbol plus what we saw last
time (and the symbol's news / data-quality / position state), emit TriggerEvents.
Pure rules, no side effects. The escalation layer decides what to DO with them.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from observation.trigger_models import TriggerEvent, TriggerSeverity, TriggerType


class TriggerRules:
    def __init__(self, obs_cfg: Dict[str, Any]) -> None:
        t = (obs_cfg or {}).get("triggers", {})
        p = t.get("price", {})
        self.price_enabled = bool(p.get("enabled", True))
        self.breakout_pct = float(p.get("breakout_above_recent_high_pct", 1.0))
        self.breakdown_pct = float(p.get("breakdown_below_recent_low_pct", -1.0))
        self.intraday_move_pct = float(p.get("intraday_move_alert_pct", 3.0))
        self.gap_pct = float(p.get("gap_alert_pct", 2.5))
        self.soft_loss = float(p.get("held_position_soft_loss_pct", -7.0))
        self.strong_loss = float(p.get("held_position_strong_loss_pct", -10.0))
        self.hard_loss = float(p.get("held_position_hard_loss_pct", -15.0))
        self.profit_review = float(p.get("held_position_profit_review_pct", 8.0))
        self.news_enabled = bool(t.get("news", {}).get("enabled", True))
        self.dq_enabled = bool(t.get("data_quality", {}).get("enabled", True))
        self.regime_enabled = bool(t.get("market_regime", {}).get("enabled", True))

    # ------------------------------------------------------------------ #
    def evaluate_symbol(
        self,
        symbol: str,
        name: Optional[str],
        market_data: Dict[str, Any],
        prev_state: Dict[str, Any],
        position: Optional[Dict[str, Any]],
        news_assessment: Optional[Dict[str, Any]],
        dq_result: Optional[Any],
        is_buy_candidate: bool,
        regime: Optional[str],
    ) -> List[TriggerEvent]:
        out: List[TriggerEvent] = []
        price = market_data.get("price")
        change_pct = market_data.get("change_pct")
        prev_close = market_data.get("previous_close")
        closes = [g.get("price") for g in market_data.get("graph", []) if g.get("price") is not None]

        def ev(ttype, sev, reason, **kw):
            out.append(TriggerEvent(symbol=symbol, company_name=name, trigger_type=ttype,
                                    severity=sev, reason=reason, price_at_detection=price,
                                    market_regime=regime, **kw))

        # ---- data quality first (blocks action) ------------------------ #
        if self.dq_enabled and dq_result is not None:
            verdict = getattr(dq_result, "verdict", None)
            if verdict == "DATA_ANOMALY":
                ev(TriggerType.DATA_ANOMALY, TriggerSeverity.HIGH,
                   "Price anomaly detected — action blocked.", blocks_action=True,
                   data_quality_flags=list(getattr(dq_result, "anomaly_flags", []) or []),
                   recommended_next_step="Block action; investigate data source.")
                return out  # don't trust other price-based triggers on bad data
            if verdict == "STALE":
                ev(TriggerType.STALE_QUOTE, TriggerSeverity.MEDIUM,
                   "Stale quote — action blocked.", blocks_action=True,
                   recommended_next_step="Block action; await fresh quote.")
                return out
            if verdict == "DATA_INSUFFICIENT" or price is None:
                ev(TriggerType.PROVIDER_FAILURE, TriggerSeverity.MEDIUM,
                   "No usable quote — provider issue.", blocks_action=True,
                   recommended_next_step="Block action; provider degraded.")
                return out

        # ---- news (high/critical) -------------------------------------- #
        if self.news_enabled and news_assessment:
            lvl = news_assessment.get("news_risk_level")
            if lvl == "CRITICAL":
                ev(TriggerType.CRITICAL_NEWS, TriggerSeverity.CRITICAL,
                   "Critical adverse news.", blocks_action=True,
                   recommended_next_step=("EXIT_REVIEW (held)" if position else "Block any buy."))
            elif lvl == "HIGH":
                ev(TriggerType.HIGH_RISK_NEWS, TriggerSeverity.HIGH,
                   "High-risk adverse news.", blocks_action=True,
                   recommended_next_step="Block any buy; review if held.")

        # ---- held-position loss / profit reviews ----------------------- #
        if position is not None:
            pnl = position.get("unrealized_pnl_pct")
            if pnl is not None:
                if pnl <= self.hard_loss:
                    ev(TriggerType.HARD_LOSS_REVIEW, TriggerSeverity.CRITICAL,
                       f"Held position at {pnl:.1f}% breaches hard-loss {self.hard_loss:.0f}%.",
                       change_pct=pnl, recommended_next_step="EXIT_REVIEW (never auto-sells).")
                elif pnl <= self.strong_loss:
                    ev(TriggerType.STRONG_LOSS_REVIEW, TriggerSeverity.HIGH,
                       f"Held position at {pnl:.1f}% breaches strong-loss {self.strong_loss:.0f}%.",
                       change_pct=pnl, recommended_next_step="TRIM_REVIEW.")
                elif pnl <= self.soft_loss:
                    ev(TriggerType.SOFT_LOSS_REVIEW, TriggerSeverity.MEDIUM,
                       f"Held position at {pnl:.1f}% breaches soft-loss {self.soft_loss:.0f}%.",
                       change_pct=pnl, recommended_next_step="SELL_REVIEW.")
                elif pnl >= self.profit_review:
                    ev(TriggerType.PROFIT_REVIEW, TriggerSeverity.LOW,
                       f"Held position up {pnl:.1f}% — review for trimming.",
                       change_pct=pnl, recommended_next_step="Consider trim (manual).")

        # ---- price action (breakout / breakdown / move / gap) ---------- #
        if self.price_enabled and price is not None:
            if closes:
                recent_high = max(closes)
                recent_low = min(closes)
                if recent_high and price > recent_high * (1 + self.breakout_pct / 100.0):
                    ev(TriggerType.PRICE_BREAKOUT, TriggerSeverity.MEDIUM,
                       f"Price {price:.2f} broke above recent high {recent_high:.2f}.",
                       requires_focused_analysis=is_buy_candidate,
                       recommended_next_step="Focused re-analysis → maybe paper buy." if is_buy_candidate else "Watch.")
                elif recent_low and price < recent_low * (1 + self.breakdown_pct / 100.0):
                    ev(TriggerType.PRICE_BREAKDOWN, TriggerSeverity.MEDIUM,
                       f"Price {price:.2f} broke below recent low {recent_low:.2f}.",
                       recommended_next_step="Caution; review if held.")
            prev_obs = prev_state.get("last_price")
            if prev_obs:
                move = (price / prev_obs - 1) * 100
                if abs(move) >= self.intraday_move_pct:
                    ev(TriggerType.LARGE_MOVE,
                       TriggerSeverity.HIGH if abs(move) >= 2 * self.intraday_move_pct else TriggerSeverity.MEDIUM,
                       f"Moved {move:+.1f}% since last observation.", change_pct=round(move, 2),
                       requires_focused_analysis=is_buy_candidate and move > 0)
            if prev_close and change_pct is not None and abs(change_pct) >= self.gap_pct:
                ev(TriggerType.GAP_MOVE, TriggerSeverity.LOW,
                   f"Gap {change_pct:+.1f}% vs previous close.", change_pct=change_pct)

        return out

    # ------------------------------------------------------------------ #
    def evaluate_regime(self, regime: Optional[str], prev_regime: Optional[str]) -> Optional[TriggerEvent]:
        if not self.regime_enabled or not regime or regime == prev_regime:
            return None
        if regime == "EVENT_RISK":
            return TriggerEvent(symbol="_MARKET_", trigger_type=TriggerType.MARKET_REGIME_SHIFT,
                                severity=TriggerSeverity.HIGH,
                                reason=f"Market regime -> EVENT_RISK (was {prev_regime}).",
                                market_regime=regime, blocks_action=True,
                                recommended_next_step="Block new buys; manual review of holdings.")
        if regime == "RISK_OFF" and prev_regime in ("RISK_ON", "NEUTRAL", None):
            return TriggerEvent(symbol="_MARKET_", trigger_type=TriggerType.MARKET_REGIME_SHIFT,
                                severity=TriggerSeverity.HIGH,
                                reason=f"Market regime {prev_regime} -> RISK_OFF.",
                                market_regime=regime, blocks_action=True,
                                recommended_next_step="Block new buys; review open positions.")
        if regime == "DATA_INSUFFICIENT":
            return TriggerEvent(symbol="_MARKET_", trigger_type=TriggerType.MARKET_REGIME_SHIFT,
                                severity=TriggerSeverity.MEDIUM,
                                reason="Market regime -> DATA_INSUFFICIENT during market hours.",
                                market_regime=regime, blocks_action=True,
                                recommended_next_step="Decline to act on insufficient data.")
        return None
