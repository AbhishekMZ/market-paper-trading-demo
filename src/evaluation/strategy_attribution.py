"""Strategy attribution leaderboard — by realized FORWARD returns.

Complements StrategyEvaluator (which attributes closed-trade P&L). This ranks
each strategy by the forward return of every episode it contributed to, which
yields far more samples than the handful of closed trades in a month.

Pure function over forward-return episodes.
"""
from __future__ import annotations

from typing import Any, Dict, List


def analyze(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    rated = [e for e in episodes if e.get("runs_tracked", 0) > 0]
    board: Dict[str, Dict[str, Any]] = {}
    for e in rated:
        ret = float(e.get("forward_return_pct", 0.0))
        for name in e.get("contributors", []) or []:
            row = board.setdefault(name, {"strategy": name, "episodes": 0, "wins": 0, "_sum": 0.0})
            row["episodes"] += 1
            row["_sum"] += ret
            if ret > 0:
                row["wins"] += 1

    rows: List[Dict[str, Any]] = []
    for row in board.values():
        n = row["episodes"]
        row["avg_forward_return_pct"] = round(row["_sum"] / n, 2) if n else 0.0
        row["hit_rate_pct"] = round(row["wins"] / n * 100, 1) if n else 0.0
        del row["_sum"]
        rows.append(row)

    # Rank by average forward return, then sample size.
    rows.sort(key=lambda r: (r["avg_forward_return_pct"], r["episodes"]), reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    return {
        "leaderboard": rows,
        "rated_episodes": len(rated),
        "note": "Ranked by average forward return of contributing signals. Indicative only; small sample.",
    }
