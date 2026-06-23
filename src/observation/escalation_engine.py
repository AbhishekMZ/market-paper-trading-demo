"""EscalationEngine — decide what to DO about triggers, safely.

Per symbol it picks the dominant trigger, applies cooldowns/throttles, optionally
runs FocusedAnalysis, and produces an EscalationItem. The ONLY way it can create
a paper trade is through the live ExecutionEngine.process_buy, which independently
enforces risk + data-quality + news + daily/monthly limits + paper-only. SELL is
review-only in v1 (never auto-sells). Real orders are impossible here.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import storage
from observation.trigger_models import (
    ActionType,
    EscalationItem,
    TriggerSeverity,
    TriggerType,
    severity_rank,
)
from order_models import OrderState
from utils import now_ist_iso

_LOSS_TYPES = {TriggerType.SOFT_LOSS_REVIEW: ActionType.SELL_REVIEW,
               TriggerType.STRONG_LOSS_REVIEW: ActionType.TRIM_REVIEW,
               TriggerType.HARD_LOSS_REVIEW: ActionType.EXIT_REVIEW}


class EscalationEngine:
    def __init__(self, obs_cfg, execution_engine, focused, cooldowns, throttle,
                 email_sender, no_action: bool = False) -> None:
        esc = (obs_cfg or {}).get("escalation", {})
        self.run_focused = bool(esc.get("run_focused_analysis_on_trigger", True))
        self.allow_paper_buy = bool(esc.get("allow_paper_buy_after_trigger", True))
        self.allow_paper_sell = bool(esc.get("allow_paper_sell_after_trigger", False))
        self.expiry_hours = float((obs_cfg or {}).get("cooldowns", {}).get("escalation_expiry_hours", 24))
        self.alert_email_enabled = bool((obs_cfg or {}).get("alerting", {}).get("email_enabled", True))
        self.send_on = (obs_cfg or {}).get("alerting", {}).get("send_on", {})
        self.engine = execution_engine
        self.focused = focused
        self.cooldowns = cooldowns
        self.throttle = throttle
        self.email = email_sender
        self.no_action = no_action
        self.max_trade = float(execution_engine.max_trade_amount)

    # ------------------------------------------------------------------ #
    def process(self, triggers: List[Any], context: Dict[str, Any]) -> Dict[str, Any]:
        by_symbol: Dict[str, List[Any]] = {}
        for t in triggers:
            by_symbol.setdefault(t.symbol, []).append(t)

        escalations: List[EscalationItem] = []
        actions_taken: List[Dict[str, Any]] = []
        blocked_actions: List[Dict[str, Any]] = []
        throttled: List[Dict[str, Any]] = []

        # Severity-first so the most urgent symbols get the limited escalation slots.
        for symbol, syms in sorted(by_symbol.items(),
                                   key=lambda kv: max(severity_rank(t.severity) for t in kv[1]), reverse=True):
            dominant = max(syms, key=lambda t: severity_rank(t.severity))
            if self.cooldowns.trigger_on_cooldown(symbol, dominant.trigger_type.value):
                throttled.append({"symbol": symbol, "trigger": dominant.trigger_type.value, "reason": "cooldown"})
                continue
            if not self.throttle.can_escalate():
                throttled.append({"symbol": symbol, "trigger": dominant.trigger_type.value, "reason": "max_escalations_per_run"})
                continue

            esc = self._decide(symbol, dominant, syms, context, actions_taken, blocked_actions)
            self.throttle.record_escalation()
            self.cooldowns.stamp_alert(symbol, dominant.trigger_type.value)
            for t in syms:
                t.created_escalation_id = esc.escalation_id
            self._maybe_email(esc, dominant, context)
            escalations.append(esc)

        return {
            "escalations": [e.to_dict() for e in escalations],
            "actions_taken": actions_taken,
            "blocked_actions": blocked_actions,
            "throttled": throttled,
            "emails_sent": self.throttle.emails_sent,
        }

    # ------------------------------------------------------------------ #
    def _decide(self, symbol, dominant, syms, context, actions_taken, blocked_actions) -> EscalationItem:
        trigger_ids = [t.trigger_id for t in syms]
        held = symbol in context.get("held_symbols", [])
        esc = EscalationItem(symbol=symbol, severity=dominant.severity, action_type=ActionType.OBSERVE_ONLY,
                             reason=dominant.reason, trigger_ids=trigger_ids,
                             expires_at=self._expiry())

        # 1) Hard blocks never act.
        if dominant.trigger_type in (TriggerType.DATA_ANOMALY, TriggerType.STALE_QUOTE, TriggerType.PROVIDER_FAILURE):
            esc.action_type = ActionType.BLOCKED_BY_DATA_QUALITY
            esc.final_decision = "No action — data not trustworthy."
            blocked_actions.append({"symbol": symbol, "blocked_by": "DATA_QUALITY", "trigger": dominant.trigger_type.value})
            return esc
        if dominant.trigger_type in (TriggerType.CRITICAL_NEWS, TriggerType.HIGH_RISK_NEWS):
            if held:
                esc.action_type = ActionType.EXIT_REVIEW if dominant.trigger_type == TriggerType.CRITICAL_NEWS else ActionType.SELL_REVIEW
                esc.manual_review_required = True
                esc.final_decision = "Adverse news on a holding — manual review (no auto-sell in v1)."
            else:
                esc.action_type = ActionType.BLOCKED_BY_NEWS
                esc.final_decision = "Adverse news — buy blocked."
            blocked_actions.append({"symbol": symbol, "blocked_by": "NEWS", "trigger": dominant.trigger_type.value})
            return esc
        if dominant.trigger_type == TriggerType.MARKET_REGIME_SHIFT:
            esc.action_type = ActionType.MANUAL_REVIEW
            esc.manual_review_required = True
            esc.final_decision = f"Regime shift ({dominant.market_regime}) — new buys blocked; review holdings."
            return esc

        # 2) Held-position loss / profit reviews (advisory; never auto-sells).
        if dominant.trigger_type in _LOSS_TYPES:
            esc.action_type = _LOSS_TYPES[dominant.trigger_type]
            esc.manual_review_required = True
            esc.final_decision = f"{esc.action_type.value} — manual only (v1 never auto-sells)."
            return esc
        if dominant.trigger_type == TriggerType.PROFIT_REVIEW:
            esc.action_type = ActionType.TRIM_REVIEW
            esc.manual_review_required = True
            esc.final_decision = "Profit-review — consider trimming (manual)."
            return esc

        # 3) Buy-candidate rechecks -> focused analysis -> maybe swift paper buy.
        if dominant.requires_focused_analysis and self.run_focused:
            esc.focused_analysis_required = True
            md = context.get("market_data_by_symbol", {}).get(symbol)
            news_raw = context.get("news_raw_by_symbol", {}).get(symbol)
            fa = self.focused.analyze(symbol, context.get("meta_by_symbol", {}).get(symbol, {}), context,
                                      market_data=md, prefetched_news=news_raw)
            esc.focused_analysis_result = fa["result"]
            sig = fa["signal"]
            res = fa["result"]
            if res["blocked_by"] == "NEWS":
                esc.action_type = ActionType.BLOCKED_BY_NEWS
                esc.final_decision = "Focused re-analysis: blocked by news."
                blocked_actions.append({"symbol": symbol, "blocked_by": "NEWS", "trigger": dominant.trigger_type.value})
            elif res["blocked_by"] == "DATA_QUALITY":
                esc.action_type = ActionType.BLOCKED_BY_DATA_QUALITY
                esc.final_decision = "Focused re-analysis: blocked by data quality."
                blocked_actions.append({"symbol": symbol, "blocked_by": "DATA_QUALITY", "trigger": dominant.trigger_type.value})
            elif res["manual_review"]:
                esc.action_type = ActionType.MANUAL_REVIEW
                esc.manual_review_required = True
                esc.final_decision = "Focused re-analysis: manual review required."
            elif res["action_allowed"]:
                esc.action_type = self._try_paper_buy(symbol, sig, fa["market_data"], context, esc, actions_taken, blocked_actions)
            else:
                esc.action_type = ActionType.OBSERVE_ONLY
                esc.final_decision = f"Focused re-analysis: {res['label']} — not a buy."
            return esc

        # 4) Everything else is informational.
        esc.action_type = ActionType.OBSERVE_ONLY
        esc.final_decision = "Logged for observation."
        return esc

    # ------------------------------------------------------------------ #
    def _try_paper_buy(self, symbol, sig, market_data, context, esc, actions_taken, blocked_actions) -> ActionType:
        if self.no_action or not self.allow_paper_buy:
            esc.final_decision = "Qualifies, but action suppressed (--no-action / config) -> review."
            return ActionType.PAPER_BUY_REVIEW
        if self.cooldowns.paper_buy_on_cooldown(symbol):
            esc.final_decision = "Qualifies, but symbol on paper-buy cooldown -> review."
            return ActionType.PAPER_BUY_REVIEW
        price = market_data.get("price")
        prices = {symbol: price}
        # The ONLY path to a paper trade — enforces risk/DQ/news/limits/paper-only.
        result = self.engine.process_buy(sig, amount_cap=self.max_trade, prices=prices, checkpoint="observe")
        if result is not None and result.status == OrderState.FILLED:
            self.cooldowns.stamp_paper_buy(symbol)
            actions_taken.append({"symbol": symbol, "action": "PAPER_BUY", "qty": result.quantity,
                                  "price": result.price, "amount": result.amount, "order_id": result.order_id})
            esc.final_decision = f"Swift paper buy: {result.quantity} @ ₹{result.price} (all gates passed)."
            return ActionType.PAPER_BUY_ALLOWED
        # process_buy returned None/!filled -> a gate (risk/limits/cap) blocked it.
        blocked_actions.append({"symbol": symbol, "blocked_by": "RISK_OR_LIMITS", "trigger": "BUY_CANDIDATE_RECHECK"})
        esc.final_decision = "Qualified on score but blocked by risk/limits at execution."
        return ActionType.BLOCKED_BY_RISK

    # ------------------------------------------------------------------ #
    def _maybe_email(self, esc: EscalationItem, dominant, context) -> None:
        if not self.alert_email_enabled or not self.email:
            return
        event = self._email_event(esc, dominant)
        if event is None or not self.send_on.get(event, True):
            return
        key = f"{esc.symbol}:{esc.action_type.value}"
        if not self.throttle.can_email(key):
            return
        subject, body = self._build_email(esc, dominant, context)
        res = self.email.send(subject, body)
        if res.get("sent"):
            esc.email_sent = True
            self.throttle.record_email(key)

    def _email_event(self, esc, dominant) -> Optional[str]:
        if dominant.severity == TriggerSeverity.CRITICAL:
            return "critical_trigger"
        if dominant.trigger_type == TriggerType.HIGH_RISK_NEWS:
            return "high_risk_news_on_position"
        if dominant.trigger_type == TriggerType.DATA_ANOMALY:
            return "data_anomaly"
        if dominant.trigger_type == TriggerType.MARKET_REGIME_SHIFT:
            return "market_regime_shift"
        if esc.action_type in (ActionType.SELL_REVIEW, ActionType.TRIM_REVIEW, ActionType.EXIT_REVIEW):
            return "position_loss_review"
        if esc.action_type in (ActionType.PAPER_BUY_ALLOWED, ActionType.PAPER_BUY_REVIEW):
            return "buy_candidate_triggered"
        return None

    def _build_email(self, esc, dominant, context):
        fa = esc.focused_analysis_result or {}
        subject = f"[Paper Observe] {dominant.severity.value} {dominant.trigger_type.value}: {esc.symbol} -> {esc.action_type.value}"
        body = "\n".join([
            f"Symbol: {esc.symbol}",
            f"Trigger: {dominant.trigger_type.value} ({dominant.severity.value})",
            f"Price/Change: {dominant.price_at_detection} / {dominant.change_pct}",
            f"Market regime: {dominant.market_regime}",
            f"Focused score: {fa.get('score')}   label: {fa.get('label')}" if fa else "Focused analysis: not run",
            f"News risk: {fa.get('news_risk_level', 'n/a')}   Data quality: {fa.get('data_quality_verdict', 'n/a')}",
            f"Action: {esc.action_type.value}",
            f"Final decision: {esc.final_decision}",
            f"Reason: {dominant.reason}",
            "",
            "Reminder: PAPER TRADING ONLY. No real order is ever placed. Sell is review-only in v1.",
        ])
        return subject, body

    def _expiry(self) -> str:
        return now_ist_iso()  # informational stamp; expiry_hours enforced on read elsewhere
