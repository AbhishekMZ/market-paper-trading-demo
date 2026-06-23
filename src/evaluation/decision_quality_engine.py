"""DecisionQualityEngine — orchestrates the evaluation layer each run.

Pulls together forward returns, shadow tracking, benchmark comparison, strategy
attribution, and threshold analysis into one `decision_quality.json`, plus a
plain-language READINESS verdict.

Hard rule: this layer only MEASURES. It never changes thresholds or weights, and
the readiness verdict NEVER enables real trading — v1 stays paper regardless.
"""
from __future__ import annotations

from typing import Any, Dict, List

import storage
from evaluation.benchmark_comparator import BenchmarkComparator
from evaluation.forward_return_tracker import ForwardReturnTracker
from evaluation import quality_metrics, shadow_tracker, strategy_attribution, threshold_analysis
from utils import now_ist_iso, write_json


class DecisionQualityEngine:
    def __init__(self, eval_cfg: Dict[str, Any]) -> None:
        cfg = eval_cfg or {}
        if isinstance(cfg.get("evaluation"), dict):
            cfg = cfg["evaluation"]            # tolerate the whole evaluation.yml mapping
        self.cfg = cfg
        self.enabled = bool(cfg.get("enabled", True))
        self.disclaimer = cfg.get("disclaimer", "Indicative only. v1 stays paper-trading.")

    # ------------------------------------------------------------------ #
    def evaluate(self, signals: List[Dict[str, Any]], prices: Dict[str, Any],
                 benchmarks: Dict[str, Any], portfolio_summary: Dict[str, Any],
                 checkpoint: str = "") -> Dict[str, Any]:
        if not self.enabled:
            return {"enabled": False, "as_of": now_ist_iso()}

        forward = ForwardReturnTracker(self.cfg)
        forward.update(signals, prices)
        forward.save()

        bench = BenchmarkComparator(self.cfg)
        bench.update(
            benchmarks,
            portfolio_total=float(portfolio_summary.get("total_value", 0.0)),
            starting_capital=float(portfolio_summary.get("starting_capital", 0.0)),
            checkpoint=checkpoint,
        )
        bench.save()

        episodes = forward.episodes()
        forward_summary = forward.summary()
        shadow = shadow_tracker.analyze(episodes, self.cfg)
        attribution = strategy_attribution.analyze(episodes)
        thresholds = threshold_analysis.analyze(episodes, self.cfg)
        comparison = bench.comparison()

        trades = storage.load_state("trade_history", [])
        trades_count = len([t for t in trades if isinstance(t, dict) and t.get("status") == "FILLED"]) \
            if isinstance(trades, list) else 0
        distinct_days = len({p.get("date") for p in bench.history if p.get("date")})

        metrics = quality_metrics.compute(forward_summary, shadow, comparison, trades_count, distinct_days)
        readiness = self._readiness(metrics, comparison, trades_count, distinct_days)

        # Observation value: did the between-checkpoint observer add signal or noise?
        obs_metrics = storage.read_json(storage.state_file("observation_metrics.json"), {})
        observation = self._observation_value(obs_metrics if isinstance(obs_metrics, dict) else {})

        payload = {
            "as_of": now_ist_iso(),
            "checkpoint": checkpoint,
            "enabled": True,
            "metrics": metrics,
            "forward_returns": forward_summary,
            "shadow": shadow,
            "benchmark": comparison,
            "attribution": attribution,
            "threshold_analysis": thresholds,
            "observation": observation,
            "readiness": readiness,
            "disclaimer": self.disclaimer,
        }
        self._write(payload)
        return payload

    # ------------------------------------------------------------------ #
    def _readiness(self, metrics, comparison, trades_count, distinct_days) -> Dict[str, Any]:
        r = self.cfg.get("readiness", {})
        min_trades = int(r.get("min_trades", 10))
        min_eps = int(r.get("min_tracked_episodes", 20))
        min_days = int(r.get("min_distinct_days", 20))
        target = float(r.get("target_benchmark_outperformance_pct", 0.0))

        checks = {
            "enough_trades": trades_count >= min_trades,
            "enough_episodes": metrics["total_tracked_episodes"] >= min_eps,
            "enough_days": distinct_days >= min_days,
        }
        reasons: List[str] = []
        if not checks["enough_trades"]:
            reasons.append(f"Only {trades_count}/{min_trades} paper trades so far.")
        if not checks["enough_episodes"]:
            reasons.append(f"Only {metrics['total_tracked_episodes']}/{min_eps} tracked episodes.")
        if not checks["enough_days"]:
            reasons.append(f"Only {distinct_days}/{min_days} distinct days of data.")

        if not all(checks.values()):
            verdict = "NOT_ENOUGH_DATA"
        else:
            outperf = comparison.get("outperformance_pct", 0.0) if comparison.get("ready") else None
            beats = outperf is not None and outperf >= target
            promising = beats and metrics["buy_grade_avg_return_pct"] > 0 and metrics["decision_edge_pct"] >= 0
            verdict = "EARLY_PROMISING" if promising else "EARLY_WEAK"
            reasons.append(
                f"Benchmark outperformance {outperf}% (target {target}%); "
                f"buy-grade avg fwd return {metrics['buy_grade_avg_return_pct']}%."
            )

        return {
            "verdict": verdict,
            "checks": checks,
            "reasons": reasons,
            "live_trading": "DISABLED",
            "note": "Readiness describes evidence maturity only. v1 stays paper-trading regardless of this verdict.",
        }

    def _observation_value(self, m: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize whether the observer is adding value or just noise."""
        triggers = int(m.get("triggers_detected", 0))
        escalations = int(m.get("escalations_created", 0))
        actions = int(m.get("paper_actions_from_triggers", 0))
        blocked = int(m.get("blocked_actions_from_triggers", 0))
        emails = int(m.get("emails_sent_total", 0))
        runs = int(m.get("observation_runs", 0))
        useful = actions + blocked  # acted-on or protectively-blocked = signal
        return {
            "observation_runs": runs,
            "triggers_detected": triggers,
            "escalations_created": escalations,
            "paper_actions_from_triggers": actions,
            "blocked_actions_from_triggers": blocked,
            "useful_triggers": useful,
            "emails_sent_total": emails,
            "alert_noise_score": round(max(0.0, (escalations - useful)) / escalations, 2) if escalations else 0.0,
            "avg_triggers_per_run": round(triggers / runs, 2) if runs else 0.0,
            "last_run": m.get("last_run"),
            "note": "Observation adds value when triggers lead to actions or protective blocks, not just alerts.",
        }

    def _write(self, payload: Dict[str, Any]) -> None:
        storage.ensure_dirs()
        write_json(storage.report_file("decision_quality.json"), payload)
        write_json(storage.public_file("decision_quality.json"), payload)
