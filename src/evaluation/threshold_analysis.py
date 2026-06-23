"""Threshold analysis — what buy threshold WOULD have worked best?

For each candidate score threshold, treat episodes with score >= T as "would
buy" and report the forward-return profile. This is purely descriptive: v1 NEVER
auto-tunes the live buy threshold (see config/scoring.yml). It exists so a human
can SEE whether the chosen threshold is well-placed.
"""
from __future__ import annotations

from typing import Any, Dict, List


def analyze(episodes: List[Dict[str, Any]], cfg: Dict[str, Any]) -> Dict[str, Any]:
    thresholds = (cfg or {}).get("thresholds_to_test", [70, 75, 80, 85, 90])
    rated = [e for e in episodes if e.get("runs_tracked", 0) > 0]

    table: List[Dict[str, Any]] = []
    for t in thresholds:
        bucket = [e for e in rated if float(e.get("score", 0)) >= t]
        rets = [float(e.get("forward_return_pct", 0.0)) for e in bucket]
        n = len(rets)
        wins = sum(1 for r in rets if r > 0)
        table.append({
            "threshold": t,
            "would_buy_count": n,
            "avg_forward_return_pct": round(sum(rets) / n, 2) if n else 0.0,
            "hit_rate_pct": round(wins / n * 100, 1) if n else 0.0,
        })

    # "Best" = highest average forward return among thresholds with a real sample.
    sampled = [r for r in table if r["would_buy_count"] >= 3]
    best = max(sampled, key=lambda r: r["avg_forward_return_pct"], default=None)

    return {
        "table": table,
        "best_threshold_observed": best["threshold"] if best else None,
        "rated_episodes": len(rated),
        "auto_tuning": "DISABLED",
        "note": (
            "Descriptive only. The live buy threshold is fixed in config/scoring.yml "
            "and is NEVER changed automatically in v1."
        ),
    }
