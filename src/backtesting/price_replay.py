"""PriceOnlyReplay — honest, PRICE-ONLY historical replay of the price-based strategies.

⚠️ DESCRIPTIVE ONLY — NOT A PROFITABILITY CLAIM.
This module reconstructs, point-in-time, the *price-based* strategy scores over
~2 years of yfinance daily bars and measures forward returns by score band. It
deliberately does NOT reproduce the live pipeline:

  * NO news overlay (news_event_risk) — historical point-in-time news is not
    available from yfinance, so it is excluded rather than fabricated.
  * NO portfolio_fit / market_regime gating, NO risk penalties, NO transaction
    costs applied to the score.
  * Weights are renormalized across the included price strategies only.

It reuses the SAME strategy plugin code as the live engine (no reimplementation)
and is strictly point-in-time: at each historical date only trailing bars up to
that date are visible (no look-ahead). Results are indicative of the price
signals' descriptive edge — they are NOT a backtest of the full system and must
never be presented as expected live performance.

See docs/strategy_validation_principles.md.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from context.features import scoring_view
from strategy.breakout import BreakoutStrategy
from strategy.mean_reversion import MeanReversionStrategy
from strategy.relative_strength import RelativeStrengthStrategy
from strategy.trend_following import TrendFollowingStrategy
from strategy.volatility_risk import VolatilityRiskStrategy
from utils import now_ist_iso

# Price-based plugins only (news_event_risk / portfolio_fit excluded on purpose).
PRICE_PLUGIN_CLASSES = {
    "trend_following": TrendFollowingStrategy,
    "relative_strength": RelativeStrengthStrategy,
    "mean_reversion": MeanReversionStrategy,
    "breakout": BreakoutStrategy,
    "volatility_risk": VolatilityRiskStrategy,
}


def _date_key(timestamp: str) -> str:
    return (timestamp or "")[:10]


class PriceOnlyReplay:
    def __init__(
        self,
        configs: Dict[str, Any],
        provider: Any,
        window: int = 22,
        horizon: int = 20,
        step: int = 5,
    ) -> None:
        scoring = configs["scoring"].get("hybrid_scoring", {})
        raw_weights = dict(scoring.get("weights", {}))
        self.buy_threshold = float(scoring.get("buy_threshold", 70))
        self.watch_threshold = float(scoring.get("watch_threshold", 60))
        self.no_action_threshold = float(scoring.get("no_action_threshold", 50))
        self.do_not_buy_threshold = float(scoring.get("do_not_buy_threshold", 35))

        # Renormalize weights across the included price strategies only.
        self.weights = {
            name: float(raw_weights.get(name, 0.0))
            for name in PRICE_PLUGIN_CLASSES
            if float(raw_weights.get(name, 0.0)) > 0
        }
        # If config zeroed a price strategy, still include it with weight 1 so the
        # replay remains meaningful (equal-weight fallback for that strategy).
        if not self.weights:
            self.weights = {name: 1.0 for name in PRICE_PLUGIN_CLASSES}

        self.plugins = {name: cls() for name, cls in PRICE_PLUGIN_CLASSES.items()}
        self.provider = provider
        self.window = int(window)
        self.horizon = int(horizon)
        self.step = max(1, int(step))

    # ------------------------------------------------------------------ #
    def _closes(self, symbol: str, lookback: str) -> List[Dict[str, Any]]:
        """Return [{'date','close'}] for usable daily bars, oldest-first."""
        snap = self.provider.get_snapshot(symbol, period=lookback, interval="1d")
        out: List[Dict[str, Any]] = []
        for bar in snap.history:
            if bar.close is not None:
                out.append({"date": _date_key(bar.timestamp), "close": float(bar.close)})
        return out

    def _score_at(
        self,
        symbol: str,
        closes: List[Dict[str, Any]],
        idx: int,
        bench_change_pct: Optional[float] = None,
        bench_closes: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[float]:
        """Point-in-time price-only score at bar index idx (uses closes[:idx+1])."""
        if idx < 1:
            return None
        trail = closes[: idx + 1]
        prev_close = closes[idx - 1]["close"]
        last_close = closes[idx]["close"]
        change_pct = ((last_close - prev_close) / prev_close * 100.0) if prev_close else 0.0
        as_of = closes[idx]["date"]
        bench_series = None
        if bench_closes:
            bench_series = [b["close"] for b in bench_closes if b["date"] <= as_of]
        feats = scoring_view([{"close": b["close"]} for b in trail], bench_closes=bench_series)
        market_data = {
            "symbol": symbol,
            "price": last_close,
            "change_pct": change_pct,
            "graph": [{"price": b["close"], "date": b["date"]} for b in trail[-self.window:]],
            "graph_points": len(trail),
            "headlines": [],
        }
        context = {"benchmark_change_pct": bench_change_pct, "hist_features": feats}

        weighted_sum = 0.0
        total_weight = 0.0
        for name, weight in self.weights.items():
            res = self.plugins[name]._safe_evaluate(symbol, market_data, {}, context)
            if not res.is_valid:
                continue
            weighted_sum += res.score_contribution * weight
            total_weight += weight
        if total_weight <= 0:
            return None
        return round(weighted_sum / total_weight, 1)

    def _band(self, score: float) -> str:
        if score >= self.buy_threshold:
            return "buy_grade"
        if score >= self.watch_threshold:
            return "watch_grade"
        if score >= self.no_action_threshold:
            return "hold_grade"
        return "low_grade"

    # ------------------------------------------------------------------ #
    def run(self, symbols: List[Dict[str, str]], lookback: str = "2y") -> Dict[str, Any]:
        bench = self._bench_change_by_date(lookback)
        try:
            bench_rows = self._closes("^NSEI", lookback)
        except Exception:
            bench_rows = []
        episodes: List[Dict[str, Any]] = []
        symbols_ok = 0
        symbols_skipped = 0

        for meta in symbols:
            symbol = meta["symbol"]
            try:
                closes = self._closes(symbol, lookback)
            except Exception:
                closes = []
            if len(closes) < self.window + self.horizon + 1:
                symbols_skipped += 1
                continue
            symbols_ok += 1

            last_scoreable = len(closes) - 1 - self.horizon
            for idx in range(self.window, last_scoreable + 1, self.step):
                date = closes[idx]["date"]
                score = self._score_at(symbol, closes, idx, bench.get(date), bench_rows)
                if score is None:
                    continue
                entry = closes[idx]["close"]
                exit_ = closes[idx + self.horizon]["close"]
                fwd_return = ((exit_ - entry) / entry * 100.0) if entry else 0.0
                episodes.append(
                    {
                        "symbol": symbol,
                        "date": date,
                        "score": score,
                        "band": self._band(score),
                        "forward_return_pct": round(fwd_return, 3),
                    }
                )

        return self._aggregate(episodes, symbols_ok, symbols_skipped, lookback)

    def _bench_change_by_date(self, lookback: str) -> Dict[str, float]:
        """Same-day % move of NIFTY 50 keyed by date, for relative strength."""
        try:
            closes = self._closes("^NSEI", lookback)
        except Exception:
            closes = []
        out: Dict[str, float] = {}
        for i in range(1, len(closes)):
            prev_c = closes[i - 1]["close"]
            if prev_c:
                out[closes[i]["date"]] = (closes[i]["close"] - prev_c) / prev_c * 100.0
        return out

    def _aggregate(
        self, episodes: List[Dict[str, Any]], symbols_ok: int, symbols_skipped: int, lookback: str
    ) -> Dict[str, Any]:
        bands: Dict[str, Dict[str, Any]] = {}
        for band in ("buy_grade", "watch_grade", "hold_grade", "low_grade"):
            rows = [e for e in episodes if e["band"] == band]
            rets = [e["forward_return_pct"] for e in rows]
            wins = [r for r in rets if r > 0]
            bands[band] = {
                "count": len(rows),
                "avg_forward_return_pct": round(sum(rets) / len(rets), 3) if rets else 0.0,
                "hit_rate_pct": round(len(wins) / len(rets) * 100.0, 1) if rets else 0.0,
                "best_pct": round(max(rets), 3) if rets else 0.0,
                "worst_pct": round(min(rets), 3) if rets else 0.0,
            }

        buy = bands["buy_grade"]
        rest = [e["forward_return_pct"] for e in episodes if e["band"] != "buy_grade"]
        rest_avg = round(sum(rest) / len(rest), 3) if rest else 0.0
        edge = round(buy["avg_forward_return_pct"] - rest_avg, 3)

        return {
            "as_of": now_ist_iso(),
            "kind": "PRICE_ONLY_HISTORICAL_REPLAY",
            "disclaimer": (
                "DESCRIPTIVE ONLY — NOT A PROFITABILITY CLAIM. Price-based strategies "
                "only; no news overlay, no regime/portfolio gating, no costs. Point-in-time "
                "(no look-ahead). Survivorship bias: uses the CURRENT index membership. "
                "See docs/strategy_validation_principles.md."
            ),
            "params": {
                "lookback": lookback,
                "window_bars": self.window,
                "forward_horizon_bars": self.horizon,
                "step_bars": self.step,
                "buy_threshold": self.buy_threshold,
                "strategies_used": sorted(self.weights.keys()),
                "renormalized_weights": self.weights,
            },
            "coverage": {
                "symbols_scored": symbols_ok,
                "symbols_skipped_insufficient_data": symbols_skipped,
                "total_episodes": len(episodes),
            },
            "by_score_band": bands,
            "buy_grade_vs_rest_edge_pct": edge,
        }
