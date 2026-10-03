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


def trailing_return_pct(closes: Sequence[float], window: int) -> Optional[float]:
    """Percent change over `window` sessions, trailing only. None if the series is short."""
    if window <= 0 or len(closes) < window + 1:
        return None
    base = closes[-(window + 1)]
    last = closes[-1]
    if not base:
        return None
    return round((last / base - 1.0) * 100.0, 3)


def excess_return_pct(
    closes: Sequence[float], bench_closes: Optional[Sequence[float]], window: int
) -> Optional[float]:
    """Stock trailing return minus the benchmark's, same window. None if either side is short."""
    if not bench_closes:
        return None
    stock = trailing_return_pct(closes, window)
    bench = trailing_return_pct(bench_closes, window)
    if stock is None or bench is None:
        return None
    return round(stock - bench, 3)


def benchmark_trailing(closes: Sequence[float]) -> Dict[str, Any]:
    """Index stats the regime engine gates on. One-day move is separate from the 20-session return."""
    vol = realized_vol(closes, 20)
    return {
        "return_1d_pct": trailing_return_pct(closes, 1),
        "return_20d_pct": trailing_return_pct(closes, 20),
        "realized_vol_20d": None if vol is None else round(vol * 100.0, 3),
    }


def scoring_view(
    bars: Sequence[Any],
    bench_closes: Optional[Sequence[float]] = None,
    cfg: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Trailing inputs for the price strategies.

    Same functions as `compute_features`, without the 250-bar overlay gate, so a
    point-in-time replay can score once the 50-session average exists. Fields
    that still lack bars stay None — callers must not substitute a 1-day move.
    """
    cfg = cfg or {}
    fcfg = cfg.get("features", {}) if isinstance(cfg.get("features"), dict) else {}
    vol_window = int(fcfg.get("vol_window", 20))
    sma50 = 50
    sma_windows = list(fcfg.get("sma_windows", [50, 200]))
    if sma_windows:
        sma50 = int(sma_windows[0])
    sma200 = int(sma_windows[1]) if len(sma_windows) > 1 else 200
    trend_lookback = int(fcfg.get("trend_lookback", 50))
    rs_window = int(fcfg.get("rs_window", 60))

    closes = close_series(bars)
    out: Dict[str, Any] = {
        "n_bars": len(closes),
        "coverage": "insufficient",
        "vol_percentile": None,
        "realized_vol_20d": None,
        "range_position_2y": None,
        "pct_above_50dma": None,
        "pct_above_200dma": None,
        "trend_persistence": None,
        "excess_return_60d": None,
    }
    if len(closes) < sma50:
        return out
    vol = realized_vol(closes, vol_window)
    out["coverage"] = "ok"
    out["vol_percentile"] = vol_percentile(closes, vol_window)
    out["realized_vol_20d"] = None if vol is None else round(vol * 100.0, 2)
    out["range_position_2y"] = range_position(closes)
    out["pct_above_50dma"] = pct_above_sma(closes, sma50)
    out["pct_above_200dma"] = pct_above_sma(closes, sma200)
    out["trend_persistence"] = trend_persistence(closes, sma50, trend_lookback)
    out["excess_return_60d"] = excess_return_pct(closes, bench_closes, rs_window)
    return out


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
    rs_window = int(fcfg.get("rs_window", 60))
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
        "excess_return_60d": None,
        "realized_vol_20d": None,
    }
    if out["coverage"] == "insufficient":
        return out

    vol = realized_vol(closes, vol_window)
    out["vol_percentile"] = vol_percentile(closes, vol_window)
    out["realized_vol_20d"] = None if vol is None else round(vol * 100.0, 2)
    out["range_position_2y"] = range_position(closes)
    out["pct_above_50dma"] = pct_above_sma(closes, sma50)
    out["pct_above_200dma"] = pct_above_sma(closes, sma200)
    out["max_drawdown_2y"] = max_drawdown(closes)
    out["current_drawdown"] = current_drawdown(closes)
    if bench_closes:
        out["beta_vs_nifty"] = beta(closes, list(bench_closes), beta_window)
    out["avg_turnover_20d"] = avg_turnover(bars, turnover_window)
    out["trend_persistence"] = trend_persistence(closes, sma50, trend_lookback)
    out["excess_return_60d"] = (
        excess_return_pct(closes, list(bench_closes), rs_window) if bench_closes else None
    )
    return out
