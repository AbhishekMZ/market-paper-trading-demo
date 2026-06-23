"""Quality metrics — the compact aggregate shown at the top of the dashboard.

Pure function; combines the forward-return summary, shadow comparison, and
benchmark comparison into a few headline numbers.
"""
from __future__ import annotations

from typing import Any, Dict


def compute(forward_summary: Dict[str, Any], shadow: Dict[str, Any],
            comparison: Dict[str, Any], trades_count: int, distinct_days: int) -> Dict[str, Any]:
    total = int(forward_summary.get("total_episodes", 0))
    acted = forward_summary.get("acted", {})
    not_acted = forward_summary.get("not_acted", {})
    buy_grade = forward_summary.get("by_score_band", {}).get("buy_grade", {})

    acted_n = int(acted.get("count", 0))
    return {
        "total_tracked_episodes": total,
        "matured_episodes": int(forward_summary.get("matured_episodes", 0)),
        "paper_trades": int(trades_count),
        "distinct_days": int(distinct_days),
        "action_rate_pct": round(acted_n / total * 100, 1) if total else 0.0,
        "avg_forward_return_acted_pct": acted.get("avg_return_pct", 0.0),
        "avg_forward_return_not_acted_pct": not_acted.get("avg_return_pct", 0.0),
        "decision_edge_pct": shadow.get("acted_vs_shadow_edge_pct", 0.0),
        "buy_grade_hit_rate_pct": buy_grade.get("hit_rate_pct", 0.0),
        "buy_grade_avg_return_pct": buy_grade.get("avg_return_pct", 0.0),
        "benchmark_outperformance_pct": comparison.get("outperformance_pct", 0.0) if comparison.get("ready") else None,
        "benchmark_verdict": comparison.get("verdict") if comparison.get("ready") else "INSUFFICIENT_DATA",
    }
