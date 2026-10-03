# Historical-Context Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compute trailing-only 2-year price features per symbol and apply them as a caution-only overlay that can downgrade a would-be paper buy or attach a flag — never creating/upgrading a buy and never changing the 0–100 score.

**Architecture:** Three small units under `src/context/` — `features.py` (pure math, no I/O), `engine.py` (`HistoricalContextEngine`: fetches 2y bars via the existing `MarketDataProvider`, computes features, caches them as committed JSON with a TTL), and `overlay.py` (`HistoricalContextOverlay`: attaches `hist_*` fields to a `TradeSignal` and downgrades only a `BUY_SMALL_PAPER`). Wired into `main.py` after the news overlay and before the buy loop; published by `static_exporter`.

**Tech Stack:** Python 3.11, stdlib only for math (`math`, `datetime`); yfinance via the existing provider; plain JSON/JSONL state (no DB). Tests are standalone scripts (`python scripts/test_*.py`) that print `OK: …` and exit 0 — the project does **not** use pytest.

**Spec:** `docs/superpowers/specs/2026-06-27-historical-context-overlay-design.md`

**Safety (binding):** No changes to `config/broker.yml`, `config/settings.yml`, or `.github/`. Caution-only. ₹0. Deterministic. Paper-only. Direct push to `main` is blocked → PR workflow; the user merges.

---

## File Structure

| File | Responsibility |
|---|---|
| `config/context.yml` (create) | Thresholds + `enabled` flag (not a safety flag). |
| `src/context/__init__.py` (create) | Package exports `HistoricalContextEngine`, `HistoricalContextOverlay`. |
| `src/context/features.py` (create) | Pure feature math. No I/O. The testable core. |
| `src/context/overlay.py` (create) | Caution-only application to a `TradeSignal`. |
| `src/context/engine.py` (create) | Fetch 2y bars + compute + TTL-cache to `data/state/historical_context.json`. |
| `src/order_models.py` (modify) | Add `hist_*` fields to `TradeSignal`. |
| `src/storage.py` (modify) | `load_all_configs()` += `context`. |
| `src/main.py` (modify) | Wire the overlay in after news, before buys. |
| `src/static_exporter.py` (modify) | Publish `historical_context.json` to `public/data`. |
| `scripts/test_historical_context.py` (create) | All tests for the above. |

Test convention (copy this runner shape — used by every task):

```python
# scripts/test_historical_context.py — run: python scripts/test_historical_context.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
```

---

### Task 1: Config file + config loading

**Files:**
- Create: `config/context.yml`
- Modify: `src/storage.py:65-77` (the `load_all_configs` dict)
- Create: `scripts/test_historical_context.py`

- [ ] **Step 1: Create `config/context.yml`**

```yaml
# =====================================================================
# Historical-context overlay configuration
# =====================================================================
# Trailing-only 2y price features, computed once/day (TTL-cached) and applied
# as a CAUTION-ONLY overlay. The overlay may downgrade a BUY to WATCH or attach
# a flag; it NEVER creates/upgrades a buy and NEVER changes the 0-100 score.
# This is NOT a backtest and makes no profitability claim.
context:
  enabled: true
  lookback_period: "2y"        # yfinance period for the history fetch
  interval: "1d"
  refresh_ttl_hours: 20         # reuse the cached snapshot within this window
  min_bars: 250                 # ~1y; below this, features are 'insufficient'
  benchmark_symbol: "^NSEI"     # for beta
  features:
    vol_window: 20
    sma_windows: [50, 200]
    beta_window: 252
    turnover_window: 20
    trend_lookback: 50
  caution:
    elevated_volatility:
      enabled: true
      vol_percentile_gte: 90
      action: "downgrade"        # downgrade | flag
    thin_liquidity:
      enabled: true
      min_avg_turnover: 50000000 # ₹5 cr/day floor; large caps clear this easily
      action: "downgrade"
    overextended:
      enabled: true
      pct_above_200dma_gte: 15
      range_position_gte: 0.95
      action: "flag"
    deep_drawdown:
      enabled: false
      current_drawdown_lte: -25
      action: "flag"
```

- [ ] **Step 2: Add `context` to `load_all_configs`**

In `src/storage.py`, inside the dict returned by `load_all_configs()`, add a line after the `"observation"` entry:

```python
        "observation": _load_optional("observation.yml"),
        "context": _load_optional("context.yml"),
    }
```

- [ ] **Step 3: Write the failing test (create the test script)**

```python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import storage


def test_config_loads():
    cfg = storage.load_all_configs().get("context", {})
    ctx = cfg.get("context", {})
    assert ctx.get("enabled") is True, "context.enabled must default to True"
    assert ctx.get("min_bars") == 250
    assert ctx["caution"]["elevated_volatility"]["action"] == "downgrade"
    assert ctx["caution"]["overextended"]["action"] == "flag"


def main():
    test_config_loads()
    print("OK: historical-context config loads")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test**

Run: `python scripts/test_historical_context.py`
Expected: `OK: historical-context config loads`

- [ ] **Step 5: Commit**

```bash
git add config/context.yml src/storage.py scripts/test_historical_context.py
git commit -m "feat(context): add context.yml config + loader wiring"
```

---

### Task 2: Pure feature math (`features.py`)

**Files:**
- Create: `src/context/__init__.py`
- Create: `src/context/features.py`
- Modify: `scripts/test_historical_context.py`

- [ ] **Step 1: Create an empty-ish package marker**

Create `src/context/__init__.py` with exactly this content (engine/overlay are added in later tasks; do NOT import them yet to avoid importing modules that don't exist):

```python
"""Historical-context overlay package."""
```

- [ ] **Step 2: Write the failing tests**

Add these functions to `scripts/test_historical_context.py` (above `main`) and call them from `main`:

```python
from context import features as F


def test_feature_math():
    # range_position: monotonic up -> 1.0 ; monotonic down -> 0.0
    up = [float(x) for x in range(100, 400)]
    down = [float(x) for x in range(400, 100, -1)]
    assert F.range_position(up) == 1.0
    assert F.range_position(down) == 0.0

    # pct_above_sma: constant series -> price == sma -> 0.0
    flat = [100.0] * 60
    assert F.pct_above_sma(flat, 50) == 0.0

    # max_drawdown / current_drawdown
    assert abs(F.max_drawdown([100.0, 110.0, 99.0]) - (-10.0)) < 1e-9
    assert abs(F.current_drawdown([100.0, 120.0, 90.0]) - (-25.0)) < 1e-9

    # beta: sym returns are exactly 2x bench returns -> beta == 2.0
    pattern = [0.01, -0.005, 0.02, -0.01, 0.015] * 60
    bench = [100.0]
    sym = [100.0]
    for r in pattern:
        bench.append(bench[-1] * (1 + r))
        sym.append(sym[-1] * (1 + 2 * r))
    assert abs(F.beta(sym, bench, 252) - 2.0) < 1e-6

    # avg_turnover: mean(close*volume) over the window
    bars = [{"close": 10.0, "volume": 100}, {"close": 20.0, "volume": 100}]
    assert F.avg_turnover(bars, 20) == 1500.0

    # trend_persistence: monotonic up -> 1.0 ; monotonic down -> 0.0
    assert F.trend_persistence(up, 50, 50) == 1.0
    assert F.trend_persistence(down, 50, 50) == 0.0

    # vol_percentile: a calm body then a volatile tail -> latest window is the
    # most volatile -> 100th percentile.
    closes = [100.0]
    for i in range(280):
        closes.append(closes[-1] * (1 + (0.001 if i % 2 == 0 else -0.001)))
    for i in range(25):
        closes.append(closes[-1] * (1 + (0.05 if i % 2 == 0 else -0.05)))
    assert F.vol_percentile(closes, 20) == 100.0


def test_compute_features_coverage():
    short = [{"close": 100.0, "volume": 10} for _ in range(10)]
    f = F.compute_features(short, bench_closes=None, cfg={"min_bars": 250})
    assert f["coverage"] == "insufficient"
    assert f["vol_percentile"] is None

    long_bars = [{"close": 100.0 + i, "volume": 1000} for i in range(300)]
    f2 = F.compute_features(long_bars, bench_closes=None, cfg={"min_bars": 250})
    assert f2["coverage"] == "ok"
    assert f2["n_bars"] == 300
    assert f2["range_position_2y"] == 1.0  # monotonic up
    assert f2["beta_vs_nifty"] is None      # no benchmark passed
```

Register them in `main`:

```python
def main():
    test_config_loads()
    test_feature_math()
    test_compute_features_coverage()
    print("OK: historical-context features")
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python scripts/test_historical_context.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'context.features'`

- [ ] **Step 4: Implement `src/context/features.py`**

```python
"""Pure, deterministic historical-context feature math (no I/O, no network).

Given a symbol's trailing daily bars (oldest -> newest) and an optional
benchmark close series, compute descriptive context features. Every function is
NaN/None-safe and returns None rather than raising when data is insufficient.

TRAILING-ONLY by construction: these read the close/volume series up to "now"
and never peek forward, so using them live introduces no look-ahead bias.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

TRADING_DAYS = 252


def _finite(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return v


def _bar_get(bar: Any, key: str) -> Any:
    val = getattr(bar, key, None)
    if val is None and isinstance(bar, dict):
        val = bar.get(key)
    return val


def close_series(bars: Sequence[Any]) -> List[float]:
    """Finite, positive close prices (oldest -> newest)."""
    out: List[float] = []
    for b in bars or []:
        c = _finite(_bar_get(b, "close"))
        if c is not None and c > 0:
            out.append(c)
    return out


def _returns(closes: Sequence[float]) -> List[float]:
    out: List[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        if prev:
            out.append(closes[i] / prev - 1.0)
    return out


def _std(xs: Sequence[float]) -> Optional[float]:
    n = len(xs)
    if n < 2:
        return None
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)  # sample variance
    return math.sqrt(var)


def _sma(closes: Sequence[float], window: int) -> Optional[float]:
    if window <= 0 or len(closes) < window:
        return None
    return sum(closes[-window:]) / window


def realized_vol(closes: Sequence[float], window: int) -> Optional[float]:
    rets = _returns(closes)
    if len(rets) < window:
        return None
    s = _std(rets[-window:])
    return None if s is None else s * math.sqrt(TRADING_DAYS)


def _rolling_vol_series(closes: Sequence[float], window: int) -> List[float]:
    rets = _returns(closes)
    out: List[float] = []
    for end in range(window, len(rets) + 1):
        s = _std(rets[end - window:end])
        if s is not None:
            out.append(s * math.sqrt(TRADING_DAYS))
    return out


def vol_percentile(closes: Sequence[float], window: int) -> Optional[float]:
    series = _rolling_vol_series(closes, window)
    if len(series) < 2:
        return None
    latest = series[-1]
    below = sum(1 for v in series if v <= latest)
    return round(below / len(series) * 100.0, 1)


def range_position(closes: Sequence[float]) -> Optional[float]:
    if len(closes) < 2:
        return None
    lo, hi = min(closes), max(closes)
    if hi <= lo:
        return None
    return round((closes[-1] - lo) / (hi - lo), 4)


def pct_above_sma(closes: Sequence[float], window: int) -> Optional[float]:
    sma = _sma(closes, window)
    if not sma:
        return None
    return round((closes[-1] / sma - 1.0) * 100.0, 2)


def max_drawdown(closes: Sequence[float]) -> Optional[float]:
    if len(closes) < 2:
        return None
    peak = closes[0]
    worst = 0.0
    for c in closes:
        if c > peak:
            peak = c
        if peak:
            dd = (c - peak) / peak * 100.0
            if dd < worst:
                worst = dd
    return round(worst, 2)


def current_drawdown(closes: Sequence[float]) -> Optional[float]:
    if len(closes) < 2:
        return None
    peak = max(closes)
    if not peak:
        return None
    return round((closes[-1] - peak) / peak * 100.0, 2)


def beta(closes: Sequence[float], bench_closes: Sequence[float], window: int) -> Optional[float]:
    rs = _returns(closes)
    rb = _returns(bench_closes)
    n = min(len(rs), len(rb), window)
    if n < 2:
        return None
    rs, rb = rs[-n:], rb[-n:]
    mean_b = sum(rb) / n
    var_b = sum((x - mean_b) ** 2 for x in rb) / (n - 1)
    if var_b <= 0:
        return None
    mean_s = sum(rs) / n
    cov = sum((rs[i] - mean_s) * (rb[i] - mean_b) for i in range(n)) / (n - 1)
    return round(cov / var_b, 3)


def avg_turnover(bars: Sequence[Any], window: int) -> Optional[float]:
    pairs: List[float] = []
    for b in bars or []:
        c = _finite(_bar_get(b, "close"))
        v = _finite(_bar_get(b, "volume"))
        if c is not None and c > 0 and v is not None and v >= 0:
            pairs.append(c * v)
    if not pairs:
        return None
    w = min(window, len(pairs))
    seg = pairs[-w:]
    return round(sum(seg) / len(seg), 2)


def trend_persistence(closes: Sequence[float], sma_window: int, lookback: int) -> Optional[float]:
    if len(closes) < sma_window + 1:
        return None
    flags: List[int] = []
    start = max(sma_window - 1, len(closes) - lookback)
    for i in range(start, len(closes)):
        window_slice = closes[i - sma_window + 1:i + 1]
        sma_i = sum(window_slice) / len(window_slice)
        if sma_i:
            flags.append(1 if closes[i] > sma_i else 0)
    if not flags:
        return None
    return round(sum(flags) / len(flags), 3)


def compute_features(
    bars: Sequence[Any],
    bench_closes: Optional[Sequence[float]] = None,
    cfg: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = cfg or {}
    fcfg = cfg.get("features", {}) if isinstance(cfg.get("features"), dict) else {}
    vol_window = int(fcfg.get("vol_window", 20))
    sma_windows = list(fcfg.get("sma_windows", [50, 200]))
    beta_window = int(fcfg.get("beta_window", 252))
    turnover_window = int(fcfg.get("turnover_window", 20))
    trend_lookback = int(fcfg.get("trend_lookback", 50))
    min_bars = int(cfg.get("min_bars", 250))
    sma50 = int(sma_windows[0]) if len(sma_windows) > 0 else 50
    sma200 = int(sma_windows[1]) if len(sma_windows) > 1 else 200

    closes = close_series(bars)
    n = len(closes)
    out: Dict[str, Any] = {
        "n_bars": n,
        "coverage_days": n,
        "coverage": "ok" if n >= min_bars else "insufficient",
        "vol_percentile": None,
        "range_position_2y": None,
        "pct_above_50dma": None,
        "pct_above_200dma": None,
        "max_drawdown_2y": None,
        "current_drawdown": None,
        "beta_vs_nifty": None,
        "avg_turnover_20d": None,
        "trend_persistence": None,
    }
    if out["coverage"] == "insufficient":
        return out

    out["vol_percentile"] = vol_percentile(closes, vol_window)
    out["range_position_2y"] = range_position(closes)
    out["pct_above_50dma"] = pct_above_sma(closes, sma50)
    out["pct_above_200dma"] = pct_above_sma(closes, sma200)
    out["max_drawdown_2y"] = max_drawdown(closes)
    out["current_drawdown"] = current_drawdown(closes)
    if bench_closes:
        out["beta_vs_nifty"] = beta(closes, list(bench_closes), beta_window)
    out["avg_turnover_20d"] = avg_turnover(bars, turnover_window)
    out["trend_persistence"] = trend_persistence(closes, sma50, trend_lookback)
    return out
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python scripts/test_historical_context.py`
Expected: `OK: historical-context features`

- [ ] **Step 6: Commit**

```bash
git add src/context/__init__.py src/context/features.py scripts/test_historical_context.py
git commit -m "feat(context): pure trailing-only feature math"
```

---

### Task 3: `TradeSignal` context fields

**Files:**
- Modify: `src/order_models.py:241-242` (insert after `news_reasons`, before `created_at`)
- Modify: `scripts/test_historical_context.py`

- [ ] **Step 1: Write the failing test**

Add to `scripts/test_historical_context.py` and register in `main`:

```python
from order_models import TradeSignal, SignalLabel, RiskLevel, DataQuality


def _signal(label=SignalLabel.BUY_SMALL_PAPER, score=82.0):
    return TradeSignal(
        signal_id="sig_test", symbol="RELIANCE.NS", name="Reliance", exchange="NSE",
        score=score, label=label, risk_level=RiskLevel.LOW, confidence=0.7,
        data_quality=DataQuality.GOOD, reason="base reason",
    )


def test_signal_has_context_fields():
    d = _signal().to_dict()
    for key in ("hist_context_available", "hist_vol_percentile", "hist_range_position",
                "hist_pct_above_200dma", "hist_beta", "hist_context_flags", "hist_context_note"):
        assert key in d, f"missing field {key}"
    assert d["hist_context_available"] is False
    assert d["hist_context_flags"] == []
    assert d["hist_context_note"] == ""
```

```python
def main():
    test_config_loads()
    test_feature_math()
    test_compute_features_coverage()
    test_signal_has_context_fields()
    print("OK: historical-context features + model")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python scripts/test_historical_context.py`
Expected: FAIL — `AssertionError: missing field hist_context_available`

- [ ] **Step 3: Add the fields**

In `src/order_models.py`, insert immediately after the `news_reasons` field and before `created_at`:

```python
    news_reasons: List[str] = field(default_factory=list)
    # Historical-context overlay (HistoricalContextOverlay). Context only ADDS caution.
    hist_context_available: bool = False
    hist_vol_percentile: Optional[float] = None
    hist_range_position: Optional[float] = None
    hist_pct_above_200dma: Optional[float] = None
    hist_beta: Optional[float] = None
    hist_context_flags: List[str] = field(default_factory=list)
    hist_context_note: str = ""
    created_at: str = field(default_factory=now_ist_iso)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python scripts/test_historical_context.py`
Expected: `OK: historical-context features + model`

- [ ] **Step 5: Commit**

```bash
git add src/order_models.py scripts/test_historical_context.py
git commit -m "feat(context): add hist_* context fields to TradeSignal"
```

---

### Task 4: Caution-only overlay (`overlay.py`)

**Files:**
- Create: `src/context/overlay.py`
- Modify: `scripts/test_historical_context.py`

- [ ] **Step 1: Write the failing tests**

Add to `scripts/test_historical_context.py` and register in `main`:

```python
from context.overlay import HistoricalContextOverlay

_OVERLAY_CFG = {
    "enabled": True,
    "caution": {
        "elevated_volatility": {"enabled": True, "vol_percentile_gte": 90, "action": "downgrade"},
        "thin_liquidity": {"enabled": True, "min_avg_turnover": 50000000, "action": "downgrade"},
        "overextended": {"enabled": True, "pct_above_200dma_gte": 15, "range_position_gte": 0.95, "action": "flag"},
        "deep_drawdown": {"enabled": False, "current_drawdown_lte": -25, "action": "flag"},
    },
}


def _features(**over):
    base = {
        "coverage": "ok", "vol_percentile": 50.0, "range_position_2y": 0.5,
        "pct_above_50dma": 2.0, "pct_above_200dma": 5.0, "max_drawdown_2y": -20.0,
        "current_drawdown": -3.0, "beta_vs_nifty": 1.1, "avg_turnover_20d": 9.9e9,
        "trend_persistence": 0.6,
    }
    base.update(over)
    return base


def test_overlay_downgrades_buy_on_elevated_vol():
    ov = HistoricalContextOverlay(_OVERLAY_CFG)
    sig = _signal(score=82.0)
    ov.apply_to_signal(sig, _features(vol_percentile=95.0))
    assert sig.label == SignalLabel.WATCH
    assert sig.score == 82.0  # score NEVER changes
    assert "elevated_volatility" in sig.hist_context_flags
    assert any("downgraded to WATCH" in w for w in sig.warnings)
    assert sig.hist_context_available is True


def test_overlay_thin_liquidity_downgrades():
    ov = HistoricalContextOverlay(_OVERLAY_CFG)
    sig = _signal(score=85.0)
    ov.apply_to_signal(sig, _features(avg_turnover_20d=1000.0))
    assert sig.label == SignalLabel.WATCH
    assert "thin_liquidity" in sig.hist_context_flags


def test_overlay_overextended_is_flag_only():
    ov = HistoricalContextOverlay(_OVERLAY_CFG)
    sig = _signal(score=82.0)
    ov.apply_to_signal(sig, _features(pct_above_200dma=20.0, range_position_2y=0.97))
    assert sig.label == SignalLabel.BUY_SMALL_PAPER  # flag action does NOT downgrade
    assert "overextended" in sig.hist_context_flags
    assert sig.score == 82.0


def test_overlay_never_upgrades_non_buy():
    ov = HistoricalContextOverlay(_OVERLAY_CFG)
    sig = _signal(label=SignalLabel.WATCH, score=60.0)
    ov.apply_to_signal(sig, _features(vol_percentile=95.0))
    assert sig.label == SignalLabel.WATCH  # downgrade rule only acts on a BUY; never upgrades
    assert sig.score == 60.0


def test_overlay_noop_on_missing_features():
    ov = HistoricalContextOverlay(_OVERLAY_CFG)
    sig = _signal(score=82.0)
    ov.apply_to_signal(sig, None)
    assert sig.label == SignalLabel.BUY_SMALL_PAPER
    assert sig.hist_context_available is False
    assert sig.hist_context_flags == []

    sig2 = _signal(score=82.0)
    ov.apply_to_signal(sig2, _features(coverage="insufficient"))
    assert sig2.label == SignalLabel.BUY_SMALL_PAPER
    assert sig2.hist_context_available is False
```

```python
def main():
    test_config_loads()
    test_feature_math()
    test_compute_features_coverage()
    test_signal_has_context_fields()
    test_overlay_downgrades_buy_on_elevated_vol()
    test_overlay_thin_liquidity_downgrades()
    test_overlay_overextended_is_flag_only()
    test_overlay_never_upgrades_non_buy()
    test_overlay_noop_on_missing_features()
    print("OK: historical-context features + model + overlay")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python scripts/test_historical_context.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'context.overlay'`

- [ ] **Step 3: Implement `src/context/overlay.py`**

```python
"""HistoricalContextOverlay — caution-only application of trailing context.

Cardinal rules (enforced, not just documented):
  * Acts ONLY on a BUY_SMALL_PAPER label. A 'downgrade' rule sets it to WATCH.
  * NEVER creates or upgrades a label. NEVER reads or writes signal.score.
  * Missing/insufficient features -> no-op (sets hist_context_available=False).
  * Exception-safe; degrades to "no context".
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from order_models import SignalLabel


class HistoricalContextOverlay:
    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        cfg = cfg or {}
        self.enabled = bool(cfg.get("enabled", True))
        caution = cfg.get("caution", {})
        self.caution = caution if isinstance(caution, dict) else {}

    # ------------------------------------------------------------------ #
    def _rule(self, name: str) -> Dict[str, Any]:
        r = self.caution.get(name, {})
        return r if isinstance(r, dict) else {}

    def evaluate(self, features: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Pure: decide which caution rules fire. Returns flags/downgrade/reasons."""
        result: Dict[str, Any] = {"flags": [], "downgrade": False, "reasons": []}
        if not self.enabled or not features or features.get("coverage") != "ok":
            return result

        def fire(name: str, reason: str) -> None:
            action = str(self._rule(name).get("action", "flag")).lower()
            result["flags"].append(name)
            result["reasons"].append(reason)
            if action == "downgrade":
                result["downgrade"] = True

        volp = features.get("vol_percentile")
        ev = self._rule("elevated_volatility")
        if ev.get("enabled", True) and volp is not None and volp >= float(ev.get("vol_percentile_gte", 90)):
            fire("elevated_volatility", f"volatility in the {volp:.0f}th percentile of 2y")

        turn = features.get("avg_turnover_20d")
        tl = self._rule("thin_liquidity")
        if tl.get("enabled", True) and turn is not None and turn < float(tl.get("min_avg_turnover", 50000000)):
            fire("thin_liquidity", f"thin liquidity (avg turnover {turn:,.0f})")

        above = features.get("pct_above_200dma")
        rangep = features.get("range_position_2y")
        oe = self._rule("overextended")
        if (oe.get("enabled", True) and above is not None and rangep is not None
                and above >= float(oe.get("pct_above_200dma_gte", 15))
                and rangep >= float(oe.get("range_position_gte", 0.95))):
            fire("overextended", f"price {above:.0f}% above 200-DMA and near 2y high")

        dd = features.get("current_drawdown")
        do = self._rule("deep_drawdown")
        if do.get("enabled", False) and dd is not None and dd <= float(do.get("current_drawdown_lte", -25)):
            fire("deep_drawdown", f"deep drawdown {dd:.0f}% from 2y peak")

        return result

    # ------------------------------------------------------------------ #
    def apply_to_signal(self, signal, features: Optional[Dict[str, Any]]) -> None:
        try:
            self._apply(signal, features)
        except Exception:
            signal.hist_context_available = False  # never break the run

    def _apply(self, signal, features: Optional[Dict[str, Any]]) -> None:
        available = bool(features) and features.get("coverage") == "ok"
        signal.hist_context_available = available
        if available:
            signal.hist_vol_percentile = features.get("vol_percentile")
            signal.hist_range_position = features.get("range_position_2y")
            signal.hist_pct_above_200dma = features.get("pct_above_200dma")
            signal.hist_beta = features.get("beta_vs_nifty")

        decision = self.evaluate(features)
        signal.hist_context_flags = list(decision["flags"])
        signal.hist_context_note = "; ".join(decision["reasons"])

        # Caution-only: only ever downgrade a BUY. Never upgrade, never touch score.
        if signal.label == SignalLabel.BUY_SMALL_PAPER and decision["downgrade"]:
            signal.label = SignalLabel.WATCH
            note = "; ".join(decision["reasons"]) or "elevated historical risk"
            signal.warnings = list(signal.warnings) + [
                f"HistContext: {note} -> buy downgraded to WATCH."
            ]
            signal.reason = "[CONTEXT] " + signal.reason
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python scripts/test_historical_context.py`
Expected: `OK: historical-context features + model + overlay`

- [ ] **Step 5: Commit**

```bash
git add src/context/overlay.py scripts/test_historical_context.py
git commit -m "feat(context): caution-only overlay (downgrade BUY only, never touches score)"
```

---

### Task 5: Engine with TTL cache (`engine.py`)

**Files:**
- Create: `src/context/engine.py`
- Modify: `src/context/__init__.py`
- Modify: `scripts/test_historical_context.py`

- [ ] **Step 1: Write the failing test**

Add to `scripts/test_historical_context.py` and register in `main`:

```python
from context.engine import HistoricalContextEngine, _hours_between
import storage

_TEST_CACHE = "_test_historical_context.json"


class _FakeProvider:
    def __init__(self, bars):
        self.bars = bars
        self.calls = 0

    def get_snapshot(self, symbol, period="1mo", interval="1d"):
        self.calls += 1

        class _Snap:
            pass

        s = _Snap()
        s.history = self.bars
        return s


def test_hours_between():
    h = _hours_between("2026-06-01T09:00:00+05:30", "2026-06-01T15:00:00+05:30")
    assert abs(h - 6.0) < 1e-6
    assert _hours_between("bad", "2026-06-01T15:00:00+05:30") is None


def test_engine_ttl_cache():
    storage.ensure_dirs()
    bars = [{"close": 100.0 + i, "volume": 1000} for i in range(300)]
    provider = _FakeProvider(bars)
    cfg = {"enabled": True, "refresh_ttl_hours": 20, "min_bars": 250,
           "benchmark_symbol": "^NSEI"}
    eng = HistoricalContextEngine(cfg, provider, usage=None, cache_filename=_TEST_CACHE)
    try:
        # First call: cold cache -> fetch (1 benchmark + 1 symbol = 2 calls).
        snap1 = eng.refresh_if_stale(["RELIANCE.NS"], now_iso="2026-06-01T09:00:00+05:30")
        first_calls = provider.calls
        assert first_calls >= 2
        assert snap1["symbols"]["RELIANCE.NS"]["coverage"] == "ok"

        # Second call within TTL (6h later): reuse cache -> NO new fetch.
        eng.refresh_if_stale(["RELIANCE.NS"], now_iso="2026-06-01T15:00:00+05:30")
        assert provider.calls == first_calls

        # Third call past TTL (2 days later): refetch.
        eng.refresh_if_stale(["RELIANCE.NS"], now_iso="2026-06-03T09:00:00+05:30")
        assert provider.calls > first_calls
    finally:
        path = storage.state_file(_TEST_CACHE)
        if os.path.exists(path):
            os.remove(path)
```

```python
def main():
    test_config_loads()
    test_feature_math()
    test_compute_features_coverage()
    test_signal_has_context_fields()
    test_overlay_downgrades_buy_on_elevated_vol()
    test_overlay_thin_liquidity_downgrades()
    test_overlay_overextended_is_flag_only()
    test_overlay_never_upgrades_non_buy()
    test_overlay_noop_on_missing_features()
    test_hours_between()
    test_engine_ttl_cache()
    print("OK: historical-context scorer, overlay, engine")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python scripts/test_historical_context.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'context.engine'`

- [ ] **Step 3: Implement `src/context/engine.py`**

```python
"""HistoricalContextEngine — fetch 2y bars, compute features, cache with a TTL.

Fetches trailing daily history (default 2y) for each symbol + the benchmark via
the injected MarketDataProvider, computes features (context.features), and caches
the result as committed JSON so the 3 daily checkpoints reuse one fetch. The
cache lives under data/state and is committed by the analyze workflow.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

import storage
from context.features import close_series, compute_features
from utils import now_ist_iso


def _hours_between(then_iso: str, now_iso: str) -> Optional[float]:
    """Hours from then_iso to now_iso, or None if either is unparseable."""
    try:
        t0 = dt.datetime.fromisoformat(then_iso)
        t1 = dt.datetime.fromisoformat(now_iso)
        return (t1 - t0).total_seconds() / 3600.0
    except (TypeError, ValueError):
        return None


class HistoricalContextEngine:
    def __init__(self, cfg, provider, usage=None, cache_filename="historical_context.json"):
        cfg = cfg or {}
        self.cfg = cfg
        self.enabled = bool(cfg.get("enabled", True))
        self.provider = provider
        self.usage = usage
        self.period = str(cfg.get("lookback_period", "2y"))
        self.interval = str(cfg.get("interval", "1d"))
        self.ttl_hours = float(cfg.get("refresh_ttl_hours", 20))
        self.benchmark_symbol = str(cfg.get("benchmark_symbol", "^NSEI"))
        self.cache_filename = cache_filename

    def _cache_path(self) -> str:
        return storage.state_file(self.cache_filename)

    def load(self) -> Dict[str, Any]:
        data = storage.read_json(self._cache_path(), {})
        return data if isinstance(data, dict) else {}

    def _is_fresh(self, cached: Dict[str, Any], now_iso: str) -> bool:
        as_of = cached.get("as_of") if isinstance(cached, dict) else None
        if not as_of:
            return False
        age = _hours_between(as_of, now_iso)
        return age is not None and 0 <= age < self.ttl_hours

    def refresh_if_stale(self, symbols: List[str], now_iso: Optional[str] = None) -> Dict[str, Any]:
        now_iso = now_iso or now_ist_iso()
        if not self.enabled:
            return {"as_of": now_iso, "ttl_hours": self.ttl_hours, "symbols": {}, "disabled": True}
        cached = self.load()
        if self._is_fresh(cached, now_iso):
            return cached
        return self._refresh(symbols, now_iso)

    def _fetch_bars(self, symbol: str) -> List[Any]:
        snap = self.provider.get_snapshot(symbol, period=self.period, interval=self.interval)
        if self.usage is not None:
            try:
                self.usage.record()
            except Exception:
                pass
        return list(getattr(snap, "history", []) or [])

    def _refresh(self, symbols: List[str], now_iso: str) -> Dict[str, Any]:
        bench_closes = close_series(self._fetch_bars(self.benchmark_symbol))
        out_symbols: Dict[str, Any] = {}
        for sym in symbols:
            try:
                bars = self._fetch_bars(sym)
                feats = compute_features(bars, bench_closes=bench_closes, cfg=self.cfg)
                feats["as_of"] = now_iso
                out_symbols[sym] = feats
            except Exception as exc:
                out_symbols[sym] = {"coverage": "insufficient", "n_bars": 0,
                                    "as_of": now_iso, "error": str(exc)}
        snapshot = {"as_of": now_iso, "ttl_hours": self.ttl_hours, "symbols": out_symbols}
        storage.write_json(self._cache_path(), snapshot)
        storage.append_audit({"event": "HISTORICAL_CONTEXT_REFRESH",
                              "symbols": len(out_symbols), "as_of": now_iso})
        return snapshot
```

- [ ] **Step 4: Export from the package**

Replace `src/context/__init__.py` with:

```python
"""Historical-context overlay package."""
from context.engine import HistoricalContextEngine
from context.overlay import HistoricalContextOverlay

__all__ = ["HistoricalContextEngine", "HistoricalContextOverlay"]
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python scripts/test_historical_context.py`
Expected: `OK: historical-context scorer, overlay, engine`

- [ ] **Step 6: Commit**

```bash
git add src/context/engine.py src/context/__init__.py scripts/test_historical_context.py
git commit -m "feat(context): engine fetches 2y bars + TTL-caches features"
```

---

### Task 6: Wire into `main.py` + publish via `static_exporter`

**Files:**
- Modify: `src/main.py` (import near line 36; overlay block after line 295)
- Modify: `src/static_exporter.py` (new export block before `return`)
- Modify: `scripts/test_historical_context.py`

- [ ] **Step 1: Write the failing test (static export)**

Add to `scripts/test_historical_context.py` and register in `main`:

```python
import static_exporter


def test_static_export_publishes_context():
    storage.ensure_dirs()
    snapshot = {"as_of": "2026-06-01T09:00:00+05:30", "ttl_hours": 20,
                "symbols": {"RELIANCE.NS": {"coverage": "ok", "vol_percentile": 42.0}}}
    storage.write_json(storage.state_file("historical_context.json"), snapshot)
    static_exporter.export_all()
    pub = os.path.join(storage.PUBLIC_DATA_DIR, "historical_context.json")
    assert os.path.exists(pub)
    got = storage.read_json(pub, {})
    assert got.get("symbols", {}).get("RELIANCE.NS", {}).get("vol_percentile") == 42.0
```

```python
def main():
    test_config_loads()
    test_feature_math()
    test_compute_features_coverage()
    test_signal_has_context_fields()
    test_overlay_downgrades_buy_on_elevated_vol()
    test_overlay_thin_liquidity_downgrades()
    test_overlay_overextended_is_flag_only()
    test_overlay_never_upgrades_non_buy()
    test_overlay_noop_on_missing_features()
    test_hours_between()
    test_engine_ttl_cache()
    test_static_export_publishes_context()
    print("OK: historical-context full suite")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python scripts/test_historical_context.py`
Expected: FAIL — `AssertionError` on `os.path.exists(pub)` (no export block yet).

- [ ] **Step 3: Add the export block to `static_exporter.py`**

In `src/static_exporter.py`, immediately before the final `return {"exported": exported, "dir": storage.PUBLIC_DATA_DIR}`:

```python
    # 5) Historical-context overlay snapshot (state -> public).
    hist = storage.read_json(storage.state_file("historical_context.json"), {})
    if hist:
        write_json(os.path.join(storage.PUBLIC_DATA_DIR, "historical_context.json"), hist)
        exported.append("historical_context.json")

    return {"exported": exported, "dir": storage.PUBLIC_DATA_DIR}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python scripts/test_historical_context.py`
Expected: `OK: historical-context full suite`

- [ ] **Step 5: Add the import to `main.py`**

In `src/main.py`, add this import alongside the other engine imports (e.g. just after `from news import NewsRiskEngine  # noqa: E402` near line 42):

```python
from context import HistoricalContextEngine, HistoricalContextOverlay  # noqa: E402
```

- [ ] **Step 6: Wire the overlay into the run**

In `src/main.py`, immediately after the news overlay block (after the line `news_health = _build_news_health(news_assessments, news_alerts, now_ist_iso(), cp_id)`) and before the comment `# --- process paper buys`, insert:

```python
    # --- historical-context overlay (post-strategy; can only ADD caution) --- #
    # Trailing-only 2y price features. Like the news overlay, this can only
    # downgrade a would-be buy or attach a flag — it never creates/upgrades a
    # buy and never changes the score. Runs BEFORE buys so a context downgrade
    # also prevents a paper buy. Wrapped so it can never break the deep run.
    try:
        ctx_cfg = (configs.get("context") or {}).get("context", {})
        if ctx_cfg.get("enabled", True):
            hist_engine = HistoricalContextEngine(ctx_cfg, provider, usage=usage)
            hist_overlay = HistoricalContextOverlay(ctx_cfg)
            hist_ctx = hist_engine.refresh_if_stale(list(market_by_symbol.keys()))
            hist_symbols = hist_ctx.get("symbols", {}) if isinstance(hist_ctx, dict) else {}
            for sig in signals:
                hist_overlay.apply_to_signal(sig, hist_symbols.get(sig.symbol))
    except Exception as exc:
        storage.append_audit({"event": "HISTORICAL_CONTEXT_ERROR", "message": str(exc)})
        print(f"[hist-context] error: {exc}", file=sys.stderr)
```

- [ ] **Step 7: Verify `main.py` still imports cleanly (offline integration check)**

Run: `python -c "import sys; sys.path.insert(0, 'src'); import main; print('import OK')"`
Expected: `import OK`

- [ ] **Step 8: Commit**

```bash
git add src/main.py src/static_exporter.py scripts/test_historical_context.py
git commit -m "feat(context): wire caution overlay into main + publish snapshot"
```

---

### Task 7: Full regression run

**Files:** none (verification only)

- [ ] **Step 1: Run the new suite**

Run: `python scripts/test_historical_context.py`
Expected: `OK: historical-context full suite`

- [ ] **Step 2: Run the existing backend suites (no regressions)**

Run each from the repo root:

```bash
python scripts/test_sentiment_scorer.py
python scripts/test_news_risk_engine.py
python scripts/test_news_event_risk_plugin.py
python scripts/test_decision_quality.py
python scripts/test_observation_engine.py
```

Expected: each prints its `OK: …` line and exits 0.

- [ ] **Step 3: Confirm safety config is untouched**

Run: `git diff --name-only origin/main -- config/broker.yml config/settings.yml .github`
Expected: empty output (no safety-relevant files changed).

- [ ] **Step 4: Commit (only if any fixes were needed; otherwise skip)**

```bash
git add -A && git commit -m "test(context): full regression green"
```

---

### Task 8 (OPTIONAL, last): Surface context on the dashboard `Why` view

Only do this if the user wants the dashboard touch. The backend is fully
functional without it. `frontend/src/views/Why.jsx` exists on `main` (merged via
PR #9).

**Files:**
- Modify: `frontend/src/views/Why.jsx`

- [ ] **Step 1: Inspect the view to match its existing render pattern**

Run: `sed -n '1,80p' frontend/src/views/Why.jsx` and find where a signal's
reasoning/fields are rendered (look for `news_` field usage to mirror it).

- [ ] **Step 2: Add a context line near the news line**

Render a single line from the signal fields, guarded so it shows nothing when
context is unavailable:

```jsx
{sig.hist_context_available && (
  <div className="why-context">
    {sig.hist_vol_percentile != null && <span>vol {Math.round(sig.hist_vol_percentile)}th pctile</span>}
    {sig.hist_range_position != null && <span> · range {(sig.hist_range_position * 100).toFixed(0)}% of 2y</span>}
    {sig.hist_beta != null && <span> · β {sig.hist_beta.toFixed(2)}</span>}
    {sig.hist_context_flags?.length > 0 && <span> · context: {sig.hist_context_flags.join(', ')}</span>}
  </div>
)}
```

- [ ] **Step 3: Build the frontend to verify it compiles**

Run: `cd frontend && npm run build`
Expected: `✓ built` with no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/Why.jsx
git commit -m "feat(context): show historical-context line on the Why view"
```

---

## Self-Review

**1. Spec coverage**

| Spec section | Task |
|---|---|
| §4 `features.py` pure math | Task 2 |
| §4 `engine.py` fetch + TTL cache | Task 5 |
| §4 `overlay.py` caution-only | Task 4 |
| §5 feature definitions | Task 2 (`compute_features` + functions) |
| §6 caution rules + invariants | Task 4 |
| §7 storage `data/state/historical_context.json` + export | Task 5 (write) + Task 6 (publish) |
| §7 tracking: per-signal embed | Task 3 (`hist_*` fields) + Task 6 (overlay attaches, `main` persists via existing `_persist_signal_history`) |
| §7 audit refresh record | Task 5 (`HISTORICAL_CONTEXT_REFRESH`) |
| §7 TTL freshness | Task 5 (`_is_fresh` / `_hours_between`) |
| §8 pipeline integration | Task 1 (config load) + Task 6 (`main.py`) |
| §9 data models | Task 3 |
| §10 degradation / exception-safety | Task 4 (`apply_to_signal` try/except), Task 5 (per-symbol try/except), Task 6 (`main` try/except) |
| §11 testing | Tasks 1–7 |
| §12 safety (no flag changes) | Task 7 Step 3 verifies |
| Optional dashboard | Task 8 |

No gaps.

**2. Placeholder scan:** No TBD/TODO/"similar to"/"add error handling" — every code step contains complete code. ✓

**3. Type consistency:** `compute_features(bars, bench_closes, cfg)`, `close_series(bars)`, `HistoricalContextEngine(cfg, provider, usage, cache_filename)` with `refresh_if_stale(symbols, now_iso)`, `_hours_between(then_iso, now_iso)`, `HistoricalContextOverlay(cfg)` with `evaluate(features)`/`apply_to_signal(signal, features)`, and the seven `hist_*` `TradeSignal` fields are referenced identically across Tasks 2–8. The cache filename `historical_context.json` and the audit event `HISTORICAL_CONTEXT_REFRESH` match between engine, exporter, and `main`. ✓
