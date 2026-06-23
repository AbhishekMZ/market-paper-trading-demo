"""Benchmark comparator — is the paper portfolio beating NIFTY?

Appends one point per run (NIFTY close + portfolio total value) to a rolling
history, then reports cumulative returns from the first recorded point. A paper
portfolio that lags the index is not adding value, however good its P&L looks in
isolation. Ledger: data/state/benchmark_history.json.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import storage
from utils import now_ist_iso, today_ist_str, write_json

_LEDGER = "benchmark_history.json"


class BenchmarkComparator:
    def __init__(self, cfg: Dict[str, Any]) -> None:
        bm = (cfg or {}).get("benchmark", {})
        self.primary_name = bm.get("primary_name", "NIFTY 50")
        self.max_points = int(bm.get("max_history_points", 500))
        self.path = storage.state_file(_LEDGER)
        hist = storage.read_json(self.path, [])
        self.history: List[Dict[str, Any]] = hist if isinstance(hist, list) else []

    def update(self, benchmarks: Dict[str, Any], portfolio_total: float,
               starting_capital: float, checkpoint: str = "") -> None:
        nifty = self._primary_close(benchmarks)
        if nifty is None and not self.history:
            return  # nothing to anchor on yet
        self.history.append({
            "date": today_ist_str(),
            "ts": now_ist_iso(),
            "checkpoint": checkpoint,
            "nifty_close": nifty,
            "portfolio_total": round(float(portfolio_total), 2),
            "starting_capital": round(float(starting_capital), 2),
        })
        self.history = self.history[-self.max_points:]

    def save(self) -> None:
        write_json(self.path, self.history)

    # ------------------------------------------------------------------ #
    def comparison(self) -> Dict[str, Any]:
        pts = [p for p in self.history if p.get("nifty_close")]
        if len(pts) < 1:
            return {"as_of": now_ist_iso(), "points": len(self.history), "ready": False,
                    "note": "Not enough benchmark history yet."}
        first, last = pts[0], pts[-1]
        base_nifty = float(first["nifty_close"])
        nifty_ret = round((float(last["nifty_close"]) / base_nifty - 1) * 100, 2) if base_nifty else 0.0
        start_cap = float(first.get("starting_capital") or last.get("starting_capital") or 0.0)
        pf_ret = round((float(last["portfolio_total"]) / start_cap - 1) * 100, 2) if start_cap else 0.0
        return {
            "as_of": now_ist_iso(),
            "ready": True,
            "points": len(pts),
            "from_date": first["date"],
            "to_date": last["date"],
            "benchmark_name": self.primary_name,
            "benchmark_return_pct": nifty_ret,
            "portfolio_return_pct": pf_ret,
            "outperformance_pct": round(pf_ret - nifty_ret, 2),
            "verdict": "AHEAD" if pf_ret > nifty_ret else ("BEHIND" if pf_ret < nifty_ret else "INLINE"),
            "history": pts[-60:],  # recent slice for a sparkline
        }

    def _primary_close(self, benchmarks: Dict[str, Any]) -> Optional[float]:
        if not isinstance(benchmarks, dict):
            return None
        md = benchmarks.get(self.primary_name)
        if isinstance(md, dict) and md.get("price"):
            return float(md["price"])
        # Fall back to the first usable benchmark.
        for v in benchmarks.values():
            if isinstance(v, dict) and v.get("ok") and v.get("price"):
                return float(v["price"])
        return None
