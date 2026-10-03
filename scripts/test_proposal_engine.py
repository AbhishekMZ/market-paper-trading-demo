"""Offline tests for the Phase 3 L1 learning proposal engine.

Run:  python scripts/test_proposal_engine.py

Asserts: propose-only labeling, allowlist/clamps, refusal to lower thresholds
when replay edge is negative, never touches live_trading / scoring.yml.
"""
from __future__ import annotations

import copy
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from evaluation.proposal_engine import ProposalEngine, STATUS_PROPOSAL  # noqa: E402
from utils import load_yaml, read_json  # noqa: E402


SCORING = {
    "hybrid_scoring": {
        "buy_threshold": 70,
        "watch_threshold": 60,
        "neutral_min_confidence": 0.50,
        "weights": {
            "trend_following": 18,
            "relative_strength": 20,
            "market_regime": 16,
            "volatility_risk": 12,
            "news_event_risk": 14,
            "portfolio_fit": 8,
            "mean_reversion": 4,
            "breakout": 8,
        },
    }
}

LEARNING_CFG = {
    "learning": {
        "auto_apply": True,  # engine must still force False
        "allowlisted_keys": [
            "hybrid_scoring.buy_threshold",
            "hybrid_scoring.watch_threshold",
            "hybrid_scoring.neutral_min_confidence",
            "hybrid_scoring.weights.trend_following",
            "hybrid_scoring.weights.relative_strength",
            "hybrid_scoring.weights.market_regime",
            "hybrid_scoring.weights.volatility_risk",
            "hybrid_scoring.weights.news_event_risk",
            "hybrid_scoring.weights.portfolio_fit",
            "hybrid_scoring.weights.mean_reversion",
            "hybrid_scoring.weights.breakout",
        ],
        "clamps": {
            "hybrid_scoring.buy_threshold": {"min": 65, "max": 90},
            "hybrid_scoring.watch_threshold": {"min": 50, "max": 80},
            "hybrid_scoring.neutral_min_confidence": {"min": 0.40, "max": 0.70},
            "weight_delta_per_strategy": 5,
            "weights_must_sum_to": 100,
        },
        "min_sample": {
            "matured_episodes": 20,
            "would_buy_count": 5,
            "strategy_episodes": 15,
            "min_replay_buy_grade_edge_pct_to_lower": 0.0,
        },
        "forbidden_keys": [
            "allow_real_orders",
            "live_trading",
            "broker.active_adapter",
            "angel_one_safety_confirmations",
        ],
    }
}


def _dq_base(**overrides):
    dq = {
        "metrics": {
            "matured_episodes": 40,
            "total_tracked_episodes": 50,
            "paper_trades": 5,
            "decision_edge_pct": 1.2,
        },
        "forward_returns": {"matured_episodes": 40},
        "threshold_analysis": {
            "best_threshold_observed": 75,
            "auto_tuning": "DISABLED",
            "table": [
                {"threshold": 70, "would_buy_count": 12, "avg_forward_return_pct": 0.5, "hit_rate_pct": 50},
                {"threshold": 75, "would_buy_count": 8, "avg_forward_return_pct": 2.0, "hit_rate_pct": 62},
            ],
        },
        "attribution": {
            "leaderboard": [
                {"strategy": "trend_following", "episodes": 40, "avg_forward_return_pct": 1.5, "hit_rate_pct": 55},
                {"strategy": "mean_reversion", "episodes": 30, "avg_forward_return_pct": -1.2, "hit_rate_pct": 30},
            ]
        },
        "shadow": {"acted_vs_shadow_edge_pct": 1.0},
        "readiness": {"verdict": "NOT_ENOUGH_DATA", "live_trading": "DISABLED"},
    }
    dq.update(overrides)
    return dq


def main() -> int:
    scoring_path = os.path.join(ROOT, "config", "scoring.yml")
    scoring_before = load_yaml(scoring_path)

    eng = ProposalEngine(LEARNING_CFG)

    # 1) Happy path: raise threshold + weight nudge; never apply.
    payload = eng.propose(
        decision_quality=_dq_base(),
        scoring=copy.deepcopy(SCORING),
        price_replay={"buy_grade_vs_rest_edge_pct": 1.5},
    )
    assert payload["status"] == STATUS_PROPOSAL
    assert payload["applied"] is False
    assert payload["auto_apply"] is False
    assert payload["live_trading"] == "DISABLED"
    keys = {p["key"] for p in payload["proposals"]}
    assert "hybrid_scoring.buy_threshold" in keys, payload["proposals"]
    assert payload["proposals"][0]["proposed"] == 75
    assert any(k.startswith("hybrid_scoring.weights.") for k in keys), keys
    for p in payload["proposals"]:
        assert p["status"] == STATUS_PROPOSAL and p["applied"] is False
        assert "live" not in p["key"].lower()
        assert "allow_real" not in p["key"].lower()
    print("ok propose raise-threshold + weights:", sorted(keys))

    # 2) Refuse to lower threshold when replay buy-grade edge is negative.
    dq_lower = _dq_base()
    dq_lower["threshold_analysis"]["best_threshold_observed"] = 65
    dq_lower["threshold_analysis"]["table"] = [
        {"threshold": 65, "would_buy_count": 20, "avg_forward_return_pct": 0.1, "hit_rate_pct": 48},
        {"threshold": 70, "would_buy_count": 12, "avg_forward_return_pct": -0.5, "hit_rate_pct": 40},
    ]
    # Clamp min is 65 — but refusal should happen before/alongside due to replay edge.
    payload2 = eng.propose(
        decision_quality=dq_lower,
        scoring=copy.deepcopy(SCORING),
        price_replay={"buy_grade_vs_rest_edge_pct": -1.15},
    )
    th_props = [p for p in payload2["proposals"] if p["key"] == "hybrid_scoring.buy_threshold"]
    assert not th_props, f"should not propose lowering: {th_props}"
    assert any("refusing to lower" in (s.get("reason") or "") for s in payload2["skipped"])
    print("ok refuse lower when replay edge negative")

    # 3) Insufficient sample → skip, still PROPOSAL envelope.
    payload3 = eng.propose(
        decision_quality=_dq_base(metrics={"matured_episodes": 3, "total_tracked_episodes": 5}),
        scoring=copy.deepcopy(SCORING),
        price_replay={},
    )
    assert payload3["proposals"] == []
    assert payload3["status"] == STATUS_PROPOSAL
    assert any("insufficient matured" in (s.get("reason") or "") for s in payload3["skipped"])
    print("ok insufficient sample skips")

    # 4) scoring.yml on disk untouched.
    scoring_after = load_yaml(scoring_path)
    assert scoring_after == scoring_before, "scoring.yml must not be mutated"
    print("ok scoring.yml untouched")

    # 5) Artifacts written with PROPOSAL label.
    report = read_json(os.path.join(ROOT, "data", "reports", "learning_proposal.json"), {})
    public = read_json(os.path.join(ROOT, "public", "data", "learning_proposal.json"), {})
    assert report.get("status") == STATUS_PROPOSAL
    assert public.get("live_trading") == "DISABLED"
    md_path = os.path.join(ROOT, "data", "reports", "learning_proposal.md")
    assert os.path.isfile(md_path)
    with open(md_path, encoding="utf-8") as fh:
        md = fh.read()
    assert "PROPOSAL" in md and "not applied" in md.lower()
    print("ok artifacts written")

    print("ALL PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
