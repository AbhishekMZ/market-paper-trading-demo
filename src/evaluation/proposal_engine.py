"""Learning proposal engine — Phase 3 L1 (PROPOSE ONLY).

Reads existing decision_quality.json (forward returns, threshold analysis,
attribution, shadow) plus optional price_replay.json and current scoring.yml,
then writes a labeled **PROPOSAL — not applied** report.

Hard rules:
  - Never mutates config/scoring.yml (or any config).
  - Never sets live_trading / allow_real_orders / Angel One flags.
  - Only allowlisted keys from config/learning.yml may appear as proposals.
  - auto_apply stays false; output always status=PROPOSAL.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import storage
from utils import now_ist_iso, write_json


STATUS_PROPOSAL = "PROPOSAL - not applied"
LIVE_DISABLED = "DISABLED"


class ProposalEngine:
    def __init__(self, learning_cfg: Optional[Dict[str, Any]] = None) -> None:
        cfg = learning_cfg or storage.load_config("learning.yml")
        if isinstance(cfg.get("learning"), dict):
            cfg = cfg["learning"]
        self.cfg = cfg or {}
        self.auto_apply = bool(self.cfg.get("auto_apply", False))
        # L1 hard override — even if someone flips the YAML, this engine never applies.
        if self.auto_apply:
            self.auto_apply = False
        self.allowlisted = set(self.cfg.get("allowlisted_keys") or [])
        self.forbidden = set(self.cfg.get("forbidden_keys") or [])
        self.clamps = dict(self.cfg.get("clamps") or {})
        self.min_sample = dict(self.cfg.get("min_sample") or {})
        self.disclaimer = self.cfg.get(
            "disclaimer",
            "PROPOSAL — not applied. Live trading remains DISABLED.",
        )

    # ------------------------------------------------------------------ #
    def propose(
        self,
        decision_quality: Optional[Dict[str, Any]] = None,
        scoring: Optional[Dict[str, Any]] = None,
        price_replay: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        dq = decision_quality if isinstance(decision_quality, dict) else self._load_decision_quality()
        scoring = scoring if isinstance(scoring, dict) else storage.load_config("scoring.yml")
        replay = price_replay if isinstance(price_replay, dict) else self._load_price_replay()

        hybrid = (scoring or {}).get("hybrid_scoring") or {}
        current = {
            "hybrid_scoring.buy_threshold": hybrid.get("buy_threshold"),
            "hybrid_scoring.watch_threshold": hybrid.get("watch_threshold"),
            "hybrid_scoring.neutral_min_confidence": hybrid.get("neutral_min_confidence"),
            "hybrid_scoring.weights": dict(hybrid.get("weights") or {}),
        }

        metrics = dq.get("metrics") or {}
        thresholds = dq.get("threshold_analysis") or {}
        attribution = dq.get("attribution") or {}
        forward = dq.get("forward_returns") or {}
        shadow = dq.get("shadow") or {}
        readiness = dq.get("readiness") or {}

        matured = int(
            metrics.get("matured_episodes")
            or forward.get("matured_episodes")
            or 0
        )
        sample = {
            "matured_episodes": matured,
            "total_tracked_episodes": int(metrics.get("total_tracked_episodes") or 0),
            "paper_trades": int(metrics.get("paper_trades") or 0),
            "decision_edge_pct": metrics.get("decision_edge_pct"),
            "readiness_verdict": readiness.get("verdict"),
            "min_matured_episodes_required": int(self.min_sample.get("matured_episodes", 20)),
        }

        proposals: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        notes: List[str] = [
            STATUS_PROPOSAL,
            "auto_apply is false — this engine never writes scoring.yml.",
            f"live_trading remains {LIVE_DISABLED}.",
        ]

        # --- buy threshold from threshold_analysis --- #
        th_props, th_skips = self._propose_buy_threshold(
            current_buy=current["hybrid_scoring.buy_threshold"],
            thresholds=thresholds,
            matured=matured,
            replay=replay,
        )
        proposals.extend(th_props)
        skipped.extend(th_skips)

        # --- weight nudges from attribution --- #
        w_props, w_skips = self._propose_weight_nudges(
            current_weights=current["hybrid_scoring.weights"],
            attribution=attribution,
            matured=matured,
        )
        proposals.extend(w_props)
        skipped.extend(w_skips)

        # Guard: strip anything forbidden / not allowlisted (defense in depth).
        clean: List[Dict[str, Any]] = []
        for p in proposals:
            key = str(p.get("key", ""))
            if self._is_forbidden(key):
                skipped.append({
                    "key": key,
                    "reason": "forbidden key (live/broker safety) — dropped",
                })
                continue
            if key not in self.allowlisted:
                skipped.append({"key": key, "reason": "not allowlisted — dropped"})
                continue
            p["status"] = STATUS_PROPOSAL
            p["applied"] = False
            clean.append(p)
        proposals = clean

        if not proposals and not any(s.get("reason", "").startswith("insufficient") for s in skipped):
            notes.append("No actionable proposals under current clamps and sample sizes.")

        if shadow:
            edge = shadow.get("acted_vs_shadow_edge_pct")
            if edge is not None:
                notes.append(f"Shadow acted-vs-declined edge: {edge}% (context only).")

        payload = {
            "as_of": now_ist_iso(),
            "kind": "LEARNING_PROPOSAL",
            "status": STATUS_PROPOSAL,
            "label": "PROPOSAL",
            "applied": False,
            "auto_apply": False,
            "live_trading": LIVE_DISABLED,
            "sample": sample,
            "current_config": current,
            "proposals": proposals,
            "skipped": skipped,
            "notes": notes,
            "inputs_used": {
                "decision_quality": bool(dq),
                "threshold_analysis": bool(thresholds),
                "attribution": bool(attribution.get("leaderboard")),
                "forward_returns": bool(forward),
                "price_replay": bool(replay),
            },
            "how_to_apply": (
                "Human only: review proposals, then `mmg.py profile apply <name>` "
                "or `mmg.py config set scoring <path> <value>`. "
                "This command never mutates scoring.yml."
            ),
            "disclaimer": self.disclaimer,
        }
        self._write(payload)
        return payload

    # ------------------------------------------------------------------ #
    def _propose_buy_threshold(
        self,
        current_buy: Any,
        thresholds: Dict[str, Any],
        matured: int,
        replay: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        key = "hybrid_scoring.buy_threshold"
        proposals: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        min_matured = int(self.min_sample.get("matured_episodes", 20))
        min_would = int(self.min_sample.get("would_buy_count", 5))

        if matured < min_matured:
            skipped.append({
                "key": key,
                "reason": f"insufficient matured episodes ({matured} < {min_matured})",
            })
            return proposals, skipped

        best = thresholds.get("best_threshold_observed")
        table = thresholds.get("table") or []
        if best is None:
            skipped.append({"key": key, "reason": "no best_threshold_observed yet"})
            return proposals, skipped

        try:
            current = float(current_buy) if current_buy is not None else None
            best_f = float(best)
        except (TypeError, ValueError):
            skipped.append({"key": key, "reason": "non-numeric threshold values"})
            return proposals, skipped

        if current is None:
            skipped.append({"key": key, "reason": "current buy_threshold missing"})
            return proposals, skipped

        row = next((r for r in table if r.get("threshold") == best or r.get("threshold") == best_f), None)
        would = int((row or {}).get("would_buy_count") or 0)
        if would < min_would:
            skipped.append({
                "key": key,
                "reason": f"insufficient would_buy_count at best threshold ({would} < {min_would})",
                "evidence": row,
            })
            return proposals, skipped

        if best_f == current:
            skipped.append({
                "key": key,
                "reason": f"best observed threshold already equals current ({current})",
            })
            return proposals, skipped

        # Safety: do not propose lowering while price-replay buy-grade edge is weak.
        replay_edge = self._replay_buy_grade_edge(replay)
        floor = float(self.min_sample.get("min_replay_buy_grade_edge_pct_to_lower", 0.0))
        if best_f < current and replay_edge is not None and replay_edge <= floor:
            skipped.append({
                "key": key,
                "reason": (
                    f"refusing to lower buy_threshold while price-replay buy-grade "
                    f"edge is {replay_edge}% (floor {floor}%)"
                ),
                "evidence": {"replay_buy_grade_edge_pct": replay_edge, "best_threshold": best_f},
            })
            return proposals, skipped

        proposed = self._clamp_value(key, best_f)
        if proposed == current:
            skipped.append({
                "key": key,
                "reason": f"clamped proposed value equals current ({current})",
            })
            return proposals, skipped

        clamp = self.clamps.get(key) or {}
        proposals.append({
            "key": key,
            "current": current,
            "proposed": proposed,
            "clamp": {"min": clamp.get("min"), "max": clamp.get("max")},
            "rationale": (
                f"Threshold analysis best_threshold_observed={best_f} "
                f"(n={would}, avg_fwd={(row or {}).get('avg_forward_return_pct')}%). "
                f"Current buy_threshold={current}."
            ),
            "evidence": {
                "best_threshold_observed": best_f,
                "would_buy_count": would,
                "avg_forward_return_pct": (row or {}).get("avg_forward_return_pct"),
                "hit_rate_pct": (row or {}).get("hit_rate_pct"),
                "replay_buy_grade_edge_pct": replay_edge,
                "auto_tuning": thresholds.get("auto_tuning", "DISABLED"),
            },
        })
        return proposals, skipped

    # ------------------------------------------------------------------ #
    def _propose_weight_nudges(
        self,
        current_weights: Dict[str, Any],
        attribution: Dict[str, Any],
        matured: int,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        proposals: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        min_matured = int(self.min_sample.get("matured_episodes", 20))
        min_eps = int(self.min_sample.get("strategy_episodes", 15))
        delta_cap = int(self.clamps.get("weight_delta_per_strategy", 5))
        must_sum = int(self.clamps.get("weights_must_sum_to", 100))

        if matured < min_matured:
            skipped.append({
                "key": "hybrid_scoring.weights.*",
                "reason": f"insufficient matured episodes ({matured} < {min_matured})",
            })
            return proposals, skipped

        board = attribution.get("leaderboard") or []
        if not board:
            skipped.append({"key": "hybrid_scoring.weights.*", "reason": "no attribution leaderboard"})
            return proposals, skipped

        eligible = [
            r for r in board
            if int(r.get("episodes") or 0) >= min_eps
            and f"hybrid_scoring.weights.{r.get('strategy')}" in self.allowlisted
            and r.get("strategy") in current_weights
        ]
        if len(eligible) < 2:
            skipped.append({
                "key": "hybrid_scoring.weights.*",
                "reason": f"need ≥2 allowlisted strategies with ≥{min_eps} episodes",
            })
            return proposals, skipped

        worst = min(eligible, key=lambda r: float(r.get("avg_forward_return_pct") or 0.0))
        best = max(eligible, key=lambda r: float(r.get("avg_forward_return_pct") or 0.0))
        if worst["strategy"] == best["strategy"]:
            skipped.append({"key": "hybrid_scoring.weights.*", "reason": "no spread between strategies"})
            return proposals, skipped

        worst_avg = float(worst.get("avg_forward_return_pct") or 0.0)
        best_avg = float(best.get("avg_forward_return_pct") or 0.0)
        if worst_avg >= 0 or best_avg <= worst_avg:
            skipped.append({
                "key": "hybrid_scoring.weights.*",
                "reason": (
                    f"no clear negative underperformer to down-weight "
                    f"(worst={worst['strategy']} {worst_avg}%)"
                ),
            })
            return proposals, skipped

        w_worst = float(current_weights.get(worst["strategy"]) or 0)
        w_best = float(current_weights.get(best["strategy"]) or 0)
        shift = min(delta_cap, max(0, int(w_worst) - 1))  # leave at least 1 if possible
        if w_worst <= 0 or shift <= 0:
            skipped.append({
                "key": f"hybrid_scoring.weights.{worst['strategy']}",
                "reason": "worst strategy already at floor weight",
            })
            return proposals, skipped

        new_worst = w_worst - shift
        new_best = w_best + shift
        # Preserve total sum.
        weights_after = dict(current_weights)
        weights_after[worst["strategy"]] = new_worst
        weights_after[best["strategy"]] = new_best
        total = sum(float(v) for v in weights_after.values())
        if abs(total - must_sum) > 0.01:
            # Renormalize lightly by adjusting best (should already sum if we only shifted).
            skipped.append({
                "key": "hybrid_scoring.weights.*",
                "reason": f"proposed weights would sum to {total}, required {must_sum}",
            })
            return proposals, skipped

        rationale = (
            f"Attribution: {worst['strategy']} avg_fwd={worst_avg}% "
            f"(n={worst.get('episodes')}) underperforms; "
            f"{best['strategy']} avg_fwd={best_avg}% (n={best.get('episodes')}). "
            f"Propose shifting {shift} weight points (clamped)."
        )
        evidence = {
            "worst": worst,
            "best": best,
            "shift": shift,
            "weights_sum_after": total,
        }

        for strat, cur, prop in (
            (worst["strategy"], w_worst, new_worst),
            (best["strategy"], w_best, new_best),
        ):
            proposals.append({
                "key": f"hybrid_scoring.weights.{strat}",
                "current": cur,
                "proposed": prop,
                "clamp": {"weight_delta_per_strategy": delta_cap, "weights_must_sum_to": must_sum},
                "rationale": rationale,
                "evidence": evidence,
            })
        return proposals, skipped

    # ------------------------------------------------------------------ #
    def _clamp_value(self, key: str, value: float) -> float:
        spec = self.clamps.get(key) or {}
        lo = spec.get("min")
        hi = spec.get("max")
        out = float(value)
        if lo is not None:
            out = max(float(lo), out)
        if hi is not None:
            out = min(float(hi), out)
        # Keep ints looking like ints for threshold keys.
        if key.endswith("threshold") and out == int(out):
            return int(out)
        return round(out, 4) if isinstance(out, float) else out

    def _is_forbidden(self, key: str) -> bool:
        k = key.lower()
        for f in self.forbidden:
            fl = f.lower().rstrip("*")
            if fl and fl in k:
                return True
            if "live" in k and "trading" in k:
                return True
            if "allow_real_orders" in k:
                return True
        return False

    @staticmethod
    def _replay_buy_grade_edge(replay: Dict[str, Any]) -> Optional[float]:
        if not replay:
            return None
        if "buy_grade_vs_rest_edge_pct" in replay:
            try:
                return float(replay["buy_grade_vs_rest_edge_pct"])
            except (TypeError, ValueError):
                return None
        bands = replay.get("by_score_band") or {}
        buy = bands.get("buy_grade") or {}
        if "avg_forward_return_pct" in buy:
            try:
                return float(buy["avg_forward_return_pct"])
            except (TypeError, ValueError):
                return None
        return None

    @staticmethod
    def _load_decision_quality() -> Dict[str, Any]:
        report = storage.read_json(storage.report_file("decision_quality.json"), {})
        public = storage.read_json(storage.public_file("decision_quality.json"), {})
        report = report if isinstance(report, dict) else {}
        public = public if isinstance(public, dict) else {}
        if not report:
            return public
        if not public:
            return report

        def _matured(d: Dict[str, Any]) -> int:
            m = d.get("metrics") or {}
            f = d.get("forward_returns") or {}
            return int(m.get("matured_episodes") or f.get("matured_episodes") or 0)

        # Prefer the richer snapshot (public/ often lags a clean local reset).
        return public if _matured(public) >= _matured(report) else report

    @staticmethod
    def _load_price_replay() -> Dict[str, Any]:
        report = storage.read_json(storage.report_file("price_replay.json"), {})
        public = storage.read_json(storage.public_file("price_replay.json"), {})
        report = report if isinstance(report, dict) else {}
        public = public if isinstance(public, dict) else {}
        return report or public

    def _write(self, payload: Dict[str, Any]) -> None:
        write_json(storage.report_file("learning_proposal.json"), payload)
        write_json(storage.public_file("learning_proposal.json"), payload)
        md = render_learning_proposal_md(payload)
        path = storage.report_file("learning_proposal.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(md)


def render_learning_proposal_md(payload: Dict[str, Any]) -> str:
    lines = [
        "# Learning Proposal",
        "",
        f"> **{payload.get('status', STATUS_PROPOSAL)}**",
        "",
        f"- As of: {payload.get('as_of')}",
        f"- Applied: `{payload.get('applied')}`",
        f"- Auto-apply: `{payload.get('auto_apply')}`",
        f"- Live trading: **{payload.get('live_trading', LIVE_DISABLED)}**",
        "",
        "## Sample",
        "",
    ]
    sample = payload.get("sample") or {}
    for k, v in sample.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Proposals", ""]
    props = payload.get("proposals") or []
    if not props:
        lines.append("_No proposals — see skipped reasons._")
    else:
        lines += [
            "| Key | Current | Proposed | Rationale |",
            "|---|---:|---:|---|",
        ]
        for p in props:
            lines.append(
                f"| `{p.get('key')}` | {p.get('current')} | {p.get('proposed')} | "
                f"{(p.get('rationale') or '').replace('|', '/')} |"
            )
    lines += ["", "## Skipped", ""]
    skips = payload.get("skipped") or []
    if not skips:
        lines.append("_None._")
    else:
        for s in skips:
            lines.append(f"- `{s.get('key')}`: {s.get('reason')}")
    lines += [
        "",
        "## How to apply",
        "",
        payload.get("how_to_apply") or "Human review only.",
        "",
        f"_{payload.get('disclaimer', '')}_",
        "",
    ]
    return "\n".join(lines)
