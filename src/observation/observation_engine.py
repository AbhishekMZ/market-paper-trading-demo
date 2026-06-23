"""ObservationEngine — lightweight, between-checkpoint monitoring.

It does NOT scan the universe. It watches only the active watchlist + open
positions, re-prices them, runs the deterministic trigger rules, and hands any
triggers to the EscalationEngine. Any swift paper action still flows through the
live ExecutionEngine (all gates enforced). Designed to be cheap and low-noise:
GitHub Actions is not a real-time engine, so v1 stays modest by design.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import storage
from observation.alert_throttle import AlertThrottle
from observation.cooldown_manager import CooldownManager
from observation.escalation_engine import EscalationEngine
from observation.focused_analysis import FocusedAnalysis
from observation.observation_state import ObservationState
from observation.trigger_models import ObservationResult
from observation.trigger_rules import TriggerRules
from observation.watchlist_manager import WatchlistManager
from utils import now_ist_iso, write_json


class ObservationEngine:
    def __init__(self, configs, provider, execution_engine, email_sender, regime_result,
                 cost_model=None, period="1mo", interval="1d", no_action=False) -> None:
        self.configs = configs
        self.obs_cfg = (configs.get("observation") or {}).get("observation", {})
        self.enabled = bool(self.obs_cfg.get("enabled", True))
        self.provider = provider
        self.execution = execution_engine
        self.email = email_sender
        self.regime = regime_result
        self.period = period
        self.interval = interval
        self.no_action = no_action
        # Reuse the SAME decision stack as the deep pipeline (cheap to build; no
        # network). The observer must never use a weaker/parallel set of gates.
        from data_quality import DataQualityEngine
        from news import NewsRiskEngine
        from strategy.hybrid_signal_engine import HybridSignalEngine
        self.hybrid = HybridSignalEngine(configs, cost_model=cost_model)
        self.news_engine = NewsRiskEngine((configs.get("news") or {}).get("news", {}))
        self.dq = DataQualityEngine(configs.get("settings", {}).get("data_quality", {}))
        self.rules = TriggerRules(self.obs_cfg)
        self.watchlist = WatchlistManager(configs)

    # ------------------------------------------------------------------ #
    def run(self, checkpoint: str, focused_symbol: Optional[str] = None) -> ObservationResult:
        mode = self.obs_cfg.get("mode", "lightweight_monitoring")
        result = ObservationResult(checkpoint=checkpoint, mode=mode)
        if not self.enabled:
            return result

        wl = self.watchlist.build_and_save()
        portfolio = storage.load_state("portfolio", {})
        positions = {p["symbol"]: p for p in portfolio.get("positions", [])}
        held = list(positions.keys())

        # Symbols to observe: watchlist + open positions (deduped). Optionally one.
        wl_by_symbol = {w["symbol"]: w for w in wl}
        symbols = list(dict.fromkeys(list(wl_by_symbol.keys()) + held))
        if focused_symbol:
            symbols = [focused_symbol]
        max_obs = int(self.obs_cfg.get("watchlist", {}).get("max_active_symbols", 15))
        symbols = symbols[:max_obs]

        obs_state = ObservationState()
        prev_regime = obs_state.last_regime
        regime_name = getattr(self.regime, "regime", None)

        triggers: List[Any] = []
        market_data_by_symbol: Dict[str, Any] = {}
        news_raw_by_symbol: Dict[str, Any] = {}
        meta_by_symbol: Dict[str, Any] = {}

        for sym in symbols:
            snap = self.provider.get_snapshot(sym, period=self.period, interval=self.interval)
            wl_item = wl_by_symbol.get(sym, {})
            md = snap.to_market_data(name=wl_item.get("name"), exchange=wl_item.get("exchange"))
            news_raw = list(getattr(snap, "news", []) or [])
            market_data_by_symbol[sym] = md
            news_raw_by_symbol[sym] = news_raw
            meta_by_symbol[sym] = wl_item

            dq_res = self.dq.assess(sym, md)
            news_a = None
            if self.obs_cfg.get("observe_news_risk", True):
                na = self.news_engine.assess(sym, md.get("name"), prefetched_news=news_raw, held=sym in held)
                news_a = na.to_dict()

            is_buy_candidate = (
                wl_item.get("priority") in ("HIGH", "HIGHEST")
                or wl_item.get("last_signal_label") in ("WATCH", "BUY_SMALL_PAPER")
                or float(wl_item.get("score_when_added") or 0) >= 70
            ) and sym not in held

            sym_triggers = self.rules.evaluate_symbol(
                sym, md.get("name"), md, obs_state.get(sym), positions.get(sym),
                news_a, dq_res, is_buy_candidate, regime_name)
            triggers.extend(sym_triggers)

            obs_state.set(sym, {"last_price": md.get("price"), "change_pct": md.get("change_pct"),
                                "news_risk_level": (news_a or {}).get("news_risk_level", "NONE"),
                                "data_quality_verdict": dq_res.verdict})

        # Market-wide regime trigger (once).
        regime_trigger = self.rules.evaluate_regime(regime_name, prev_regime)
        if regime_trigger is not None:
            triggers.append(regime_trigger)

        # ---- escalation ------------------------------------------------- #
        cooldowns = CooldownManager(self.obs_cfg)
        throttle = AlertThrottle(self.obs_cfg)
        focused = FocusedAnalysis(self.configs, self.provider, self.hybrid, self.news_engine, self.dq,
                                  period=self.period, interval=self.interval)
        escalator = EscalationEngine(self.obs_cfg, self.execution, focused, cooldowns, throttle,
                                     self.email, no_action=self.no_action)
        context = self._context(checkpoint, held, portfolio, meta_by_symbol,
                                market_data_by_symbol, news_raw_by_symbol)
        esc_out = escalator.process(triggers, context)
        cooldowns.save()

        obs_state.mark_observation(regime_name)
        obs_state.save()

        result.observed_symbols = symbols
        result.open_positions_observed = [s for s in symbols if s in held]
        result.triggers = [t.to_dict() for t in triggers]
        result.throttled = esc_out["throttled"]
        result.escalations = esc_out["escalations"]
        result.actions_taken = esc_out["actions_taken"]
        result.blocked_actions = esc_out["blocked_actions"]
        result.emails_sent = esc_out["emails_sent"]

        self._persist(result, wl)
        return result

    # ------------------------------------------------------------------ #
    def _context(self, checkpoint, held, portfolio, meta_by_symbol, md_by_symbol, news_by_symbol) -> Dict[str, Any]:
        cap = self.configs.get("settings", {}).get("capital", {})
        budget = storage.load_state("monthly_budget", {})
        exec_state = storage.load_state("execution_state", {})
        return {
            "regime": self.regime,
            "held_symbols": held,
            "portfolio": portfolio,
            "budget": budget,
            "limits": {
                "max_trade_amount": float(cap.get("max_amount_per_trade", 2000)),
                "max_buys_per_day": int(cap.get("max_buys_per_day", 1)),
                "max_buys_per_month": int(cap.get("max_buys_per_month", 5)),
            },
            "buys_today": exec_state.get("buys_today", 0),
            "checkpoint": checkpoint,
            "meta_by_symbol": meta_by_symbol,
            "market_data_by_symbol": md_by_symbol,
            "news_raw_by_symbol": news_by_symbol,
        }

    # ------------------------------------------------------------------ #
    def _persist(self, result: ObservationResult, watchlist: List[Dict[str, Any]]) -> None:
        # Rolling trigger history.
        hist = storage.read_json(storage.state_file("trigger_history.json"), [])
        if not isinstance(hist, list):
            hist = []
        hist.extend(result.triggers)
        hist = hist[-500:]
        write_json(storage.state_file("trigger_history.json"), hist)

        # Escalation queue: rolling (recent escalations persist across runs, so a
        # cooldown-throttled later run doesn't wipe earlier items). Capped.
        queue = storage.read_json(storage.state_file("escalation_queue.json"), [])
        if not isinstance(queue, list):
            queue = []
        queue.extend(result.escalations)
        queue = queue[-100:]
        write_json(storage.state_file("escalation_queue.json"), queue)

        # Cumulative metrics (feeds the Decision Quality Engine + dashboard).
        metrics = storage.read_json(storage.state_file("observation_metrics.json"), {})
        if not isinstance(metrics, dict):
            metrics = {}
        metrics["observation_runs"] = int(metrics.get("observation_runs", 0)) + 1
        metrics["triggers_detected"] = int(metrics.get("triggers_detected", 0)) + len(result.triggers)
        metrics["escalations_created"] = int(metrics.get("escalations_created", 0)) + len(result.escalations)
        metrics["paper_actions_from_triggers"] = int(metrics.get("paper_actions_from_triggers", 0)) + len(result.actions_taken)
        metrics["blocked_actions_from_triggers"] = int(metrics.get("blocked_actions_from_triggers", 0)) + len(result.blocked_actions)
        metrics["emails_sent_total"] = int(metrics.get("emails_sent_total", 0)) + result.emails_sent
        metrics["last_run"] = now_ist_iso()
        metrics["last_watchlist_size"] = len(watchlist)
        write_json(storage.state_file("observation_metrics.json"), metrics)

        report = {
            "as_of": now_ist_iso(), "checkpoint": result.checkpoint, "mode": result.mode,
            "watchlist_size": len(watchlist), "observed": len(result.observed_symbols),
            "open_positions_observed": len(result.open_positions_observed),
            "triggers_this_run": len(result.triggers), "escalations": len(result.escalations),
            "actions_taken": result.actions_taken, "blocked_actions": result.blocked_actions,
            "throttled": len(result.throttled), "emails_sent": result.emails_sent,
            "metrics": metrics, "result": result.to_dict(),
        }
        esc_report = {
            "as_of": now_ist_iso(), "checkpoint": result.checkpoint,
            "open_escalations": result.escalations,
            "actions_taken": result.actions_taken, "blocked_actions": result.blocked_actions,
        }
        write_json(storage.report_file("observation_report.json"), report)
        write_json(storage.report_file("escalation_report.json"), esc_report)
        self._write_markdown(report, esc_report)

        # Public exports (capped, newest-first where it is a list).
        write_json(storage.public_file("observation_report.json"), report)
        write_json(storage.public_file("escalation_report.json"), esc_report)
        write_json(storage.public_file("active_watchlist.json"), watchlist)
        write_json(storage.public_file("observation_state.json"), ObservationState().data)
        write_json(storage.public_file("trigger_history.json"), hist[-300:][::-1])
        write_json(storage.public_file("escalation_queue.json"), queue[-100:][::-1])

    def _write_markdown(self, report, esc_report) -> None:
        lines = [
            "# Observation Report", "", f"_As of {report['as_of']} — checkpoint {report['checkpoint']}_", "",
            f"- Mode: **{report['mode']}**",
            f"- Watchlist size: **{report['watchlist_size']}**  |  Observed: **{report['observed']}**",
            f"- Triggers this run: **{report['triggers_this_run']}**  |  Escalations: **{report['escalations']}**",
            f"- Paper actions: **{len(report['actions_taken'])}**  |  Blocked: **{len(report['blocked_actions'])}**  |  Emails: **{report['emails_sent']}**",
            "", "> PAPER TRADING ONLY. Swift action means swift PAPER action or a manual-review alert — never a real order.",
        ]
        with open(storage.report_file("observation_report.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        with open(storage.report_file("escalation_report.md"), "w", encoding="utf-8") as fh:
            fh.write(f"# Escalation Report\n\n_As of {esc_report['as_of']}_\n\n"
                     f"- Open escalations: {len(esc_report['open_escalations'])}\n"
                     f"- Paper actions: {len(esc_report['actions_taken'])}\n"
                     f"- Blocked actions: {len(esc_report['blocked_actions'])}\n")
