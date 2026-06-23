"""Decision Quality Engine — measures whether the system's decisions are good.

Public surface:
    DecisionQualityEngine — evaluate(signals, prices, benchmarks, portfolio_summary)
    ForwardReturnTracker  — per-symbol forward-return episodes (the measurement spine)
    BenchmarkComparator   — portfolio vs NIFTY over time

Design invariant: this layer only MEASURES. It never auto-tunes thresholds or
weights, and its readiness verdict never enables real trading (v1 stays paper).
"""
from __future__ import annotations

from evaluation.benchmark_comparator import BenchmarkComparator
from evaluation.decision_quality_engine import DecisionQualityEngine
from evaluation.forward_return_tracker import ForwardReturnTracker

__all__ = ["DecisionQualityEngine", "ForwardReturnTracker", "BenchmarkComparator"]
