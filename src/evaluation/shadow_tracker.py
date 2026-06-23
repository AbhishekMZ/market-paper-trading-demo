"""Shadow tracker — did our DECISIONS (act vs decline) add value?

Compares the forward returns of:
  * acted episodes (we placed a paper buy), vs
  * shadow episodes (strong candidates we declined: high WATCH, or buys blocked
    by news / data-quality), vs
  * blocked episodes specifically (did blocking protect us?).

A protective block shows a NEGATIVE average forward return (we correctly avoided
a loser); a costly block shows a positive one (we missed a winner). Pure function
over forward-return episodes — no state of its own.
"""
from __future__ import annotations

from typing import Any, Dict, List

from evaluation.forward_return_tracker import ForwardReturnTracker


def _stat(eps: List[Dict[str, Any]]) -> Dict[str, Any]:
    return ForwardReturnTracker._stat(eps)


def analyze(episodes: List[Dict[str, Any]], cfg: Dict[str, Any]) -> Dict[str, Any]:
    strong = float((cfg or {}).get("shadow", {}).get("strong_watch_threshold", 65))

    acted = [e for e in episodes if e.get("acted")]
    not_acted = [e for e in episodes if not e.get("acted")]
    shadow_candidates = [
        e for e in not_acted
        if float(e.get("score", 0)) >= strong or e.get("news_blocked")
        or e.get("data_quality_verdict", "OK") != "OK"
    ]
    blocked = [
        e for e in episodes
        if e.get("news_blocked") or e.get("data_quality_verdict", "OK") != "OK"
    ]

    acted_stat = _stat(acted)
    shadow_stat = _stat(shadow_candidates)
    blocked_stat = _stat(blocked)

    # Was declining the right call? Compare acted vs shadow average return.
    edge = round(acted_stat["avg_return_pct"] - shadow_stat["avg_return_pct"], 2)
    if not acted_stat["rated"] or not shadow_stat["rated"]:
        decision_note = "Not enough matured episodes on both sides to compare yet."
    elif edge > 0:
        decision_note = f"Acted picks outperformed declined candidates by {edge}% avg forward return."
    elif edge < 0:
        decision_note = f"Declined candidates would have outperformed acted picks by {abs(edge)}% — review selectivity."
    else:
        decision_note = "Acted and declined candidates performed in line so far."

    if not blocked_stat["rated"]:
        block_note = "No matured blocked episodes yet."
    elif blocked_stat["avg_return_pct"] <= 0:
        block_note = f"Blocks were protective on average ({blocked_stat['avg_return_pct']}% forward return avoided)."
    else:
        block_note = f"Blocked names rose {blocked_stat['avg_return_pct']}% on average — blocking had a cost (still paper-safe)."

    return {
        "acted": acted_stat,
        "shadow_candidates": shadow_stat,
        "blocked": blocked_stat,
        "acted_vs_shadow_edge_pct": edge,
        "decision_note": decision_note,
        "block_note": block_note,
        "shadow_examples": sorted(
            shadow_candidates, key=lambda e: float(e.get("forward_return_pct", 0.0)), reverse=True
        )[:8],
    }
