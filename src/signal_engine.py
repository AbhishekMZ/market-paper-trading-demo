"""DEPRECATED facade — kept for backward compatibility.

The monolithic signal engine was refactored into a modular, plugin-based
strategy layer. The system now scores symbols with HybridSignalEngine, which
combines independent strategy plugins (see src/strategy/).

Use:
    from strategy.hybrid_signal_engine import HybridSignalEngine

This module simply re-exports it under the old name so older imports keep
working. There is intentionally NO monolithic scoring logic here anymore.
"""
from __future__ import annotations

from strategy.hybrid_signal_engine import HybridSignalEngine

# Backwards-compatible alias.
SignalEngine = HybridSignalEngine

__all__ = ["SignalEngine", "HybridSignalEngine"]
