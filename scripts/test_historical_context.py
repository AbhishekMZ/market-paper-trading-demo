# scripts/test_historical_context.py — run: python scripts/test_historical_context.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import storage
import static_exporter
from context import features as F
from context.overlay import HistoricalContextOverlay
from context.engine import HistoricalContextEngine, _hours_between
from order_models import TradeSignal, SignalLabel, RiskLevel, DataQuality


def test_config_loads():
    cfg = storage.load_all_configs().get("context", {})
    ctx = cfg.get("context", {})
    assert ctx.get("enabled") is True, "context.enabled must default to True"
    assert ctx.get("min_bars") == 250
    assert ctx["caution"]["elevated_volatility"]["action"] == "downgrade"
    assert ctx["caution"]["overextended"]["action"] == "flag"


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


def main():
    import tempfile

    # Isolate state/public writes from the live paper ledger + Pages export.
    storage.redirect_runtime_dirs(tempfile.mkdtemp(prefix="mmg_hist_test_"))
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


if __name__ == "__main__":
    main()
