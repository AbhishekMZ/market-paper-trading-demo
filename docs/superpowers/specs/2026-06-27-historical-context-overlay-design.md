# Historical-Context Overlay — Design Spec

**Date:** 2026-06-27
**Status:** Approved (design) — pending plan + implementation
**Author:** pair-designed with Claude

## 1. Goal

Use **2 years of price history** to compute per-symbol, *trailing-only* contextual
features and feed them into the live decision pipeline as a **caution-only
overlay** — mirroring the existing `NewsRiskEngine`. The overlay enriches every
signal with descriptive context and may **add caution** (downgrade a would-be
paper buy, or attach a flag) but can **never** create or upgrade a buy and
**never** changes the 0–100 score.

This is *not* a historical strategy backtest. It makes **no profitability
claim**. It is descriptive context that frames each live decision.

## 2. Background & why this is safe

`src/backtesting/` deliberately leaves `replay_full_history()` and the
walk-forward validator as `NotImplementedError` placeholders.
`docs/strategy_validation_principles.md` explains why: a real historical
backtest needs a point-in-time, survivorship-bias-free universe and historical
news/fundamentals we do not have (yfinance returns only *current* news). Building
it on biased free data is worse than not building it.

This feature sidesteps every one of those landmines because it is **not** a
backtest:

- **No survivorship bias.** We only ever describe the *current* watchlist going
  forward; we never test a historical universe's returns.
- **No look-ahead bias.** Every feature is computed from data *trailing* the
  decision moment. When used live, "now" is the present, so only past data is
  ever read. The features are also stored on the signal at decision time and
  never mutated afterward (the project's append-only rule).
- **No historical news needed.** Features are price/volume only.
- **No overfitting.** The overlay never touches the score and never tunes
  weights; it can only add caution via fixed, configurable thresholds.

What *changed* to make this possible: the project moved from SerpApi to
**yfinance**, which serves 2 years of split/dividend-adjusted daily **price**
bars for the watchlist at ₹0. The data blocker the backtesting README cited is
gone — for price data.

## 3. Scope

**In scope**
- A pure feature-computation module (no I/O), an engine that fetches + caches 2y
  bars and computes features, and a caution-only overlay that applies them.
- Persistence as committed JSON; tracking via per-signal embedding + git + audit.
- Config, data-model fields, pipeline wiring, static export, tests.
- *Optional, last task:* surface the context line on the dashboard `Why` view.

**Out of scope (explicitly)**
- Any change to the 0–100 score or strategy weights.
- Any historical strategy backtest / P&L simulation / walk-forward.
- Raw 2y bars as a committed data lake (raw bars are an ephemeral fetch).
- A database / backend. Storage stays committed JSON. A backend+DB migration is
  a **separate, future sub-project** (recorded in memory: `backend-db-migration-plan`).

## 4. Architecture & components

```
config/context.yml ──► HistoricalContextEngine ──► historical_context.json (state, committed)
  (thresholds)            │  fetch 2y bars (yfinance, daily, TTL-cached)        │
                          │  features.py (pure math)                           │
                          ▼                                                     ▼
   per-symbol features ──► HistoricalContextOverlay.apply_to_signal ──► TradeSignal.hist_*
                              (caution-only: downgrade BUY→WATCH / flag)        │
                                                                                ▼
                                              signal_history.json (append-only) + public/data
```

Three small, single-responsibility units:

- **`src/context/features.py`** — pure functions: given a symbol's bars (and an
  optional benchmark close series), return a features dict. No I/O, no network,
  deterministic, NaN-safe. The testable core.
- **`src/context/engine.py`** — `HistoricalContextEngine`: orchestrates the 2y
  fetch (via the injected `MarketDataProvider`), calls `features.py`, and
  read/writes the cached `historical_context.json` with a freshness TTL.
- **`src/context/overlay.py`** — `HistoricalContextOverlay`: pure rule
  evaluation + `apply_to_signal` that attaches `hist_*` fields and, for a
  `BUY_SMALL_PAPER` label only, may downgrade to `WATCH` / add a flag.

## 5. Feature definitions (trailing-only, from 2y daily bars)

All computed from the close series `c[0..n-1]` (oldest→newest); volume from bars.
`r[i] = c[i]/c[i-1] - 1`. Configurable windows in `config/context.yml`.

| Feature | Definition |
|---|---|
| `vol_percentile` | Rolling 20-day annualized realized vol `σ_t = std(r[t-19..t]) * √252`; report the percentile rank of the latest `σ` within the full 2y series of `σ_t` (0–100). |
| `range_position_2y` | `(c[-1] − min(c)) / (max(c) − min(c))`, clamped 0–1. |
| `pct_above_50dma`, `pct_above_200dma` | `(c[-1] / SMA(window) − 1) * 100`. |
| `max_drawdown_2y` | Most negative `(c[i] − peak_so_far)/peak_so_far * 100` over the series. |
| `current_drawdown` | `(c[-1] − max(c)) / max(c) * 100` (≤ 0). |
| `beta_vs_nifty` | `cov(r_sym, r_bench) / var(r_bench)` over the last `beta_window` (≈252) aligned returns; `None` if insufficient/zero-variance. |
| `avg_turnover_20d` | `mean(close·volume)` over the last 20 bars (liquidity proxy). |
| `trend_persistence` | fraction of the last 50 closes that are above their own 50-DMA (0–1). |
| provenance | `n_bars`, `coverage_days`, `coverage` ∈ {`ok`,`insufficient`}, `as_of` (set by engine). |

**Insufficiency:** if `n_bars < min_bars` (default 250 ≈ 1y), `coverage =
"insufficient"`, all derived features are `None`, and the overlay no-ops.

## 6. Caution rules (overlay — only ever downgrade or flag)

All configurable in `config/context.yml`, all OR'd. Each rule has an `action`:
`downgrade` (BUY→WATCH + flag + reason) or `flag` (attach flag only).

| Rule | Fires when | Default action |
|---|---|---|
| `elevated_volatility` | `vol_percentile ≥ 90` | downgrade |
| `thin_liquidity` | `avg_turnover_20d < min_avg_turnover` | downgrade |
| `overextended` | `pct_above_200dma ≥ 15` **and** `range_position_2y ≥ 0.95` | flag |
| `deep_drawdown` (default off) | `current_drawdown ≤ −25` | flag |

**Hard invariants (mirrors `NewsRiskEngine`):**
1. Acts only when `signal.label == BUY_SMALL_PAPER`. A `downgrade` sets it to
   `WATCH`. No rule ever produces a "more positive" label.
2. Never creates a buy, never upgrades any label.
3. Never reads or writes `signal.score`.
4. `features is None` or `coverage == "insufficient"` → attach
   `hist_context_available = False` and return (no behavior change).
5. Every path is exception-safe; a failure degrades to "no context".

## 7. Storage & tracking

- **Cache / source of truth:** `data/state/historical_context.json` via
  `storage.state_file("historical_context.json")` (ad-hoc state file, like
  `benchmark_history.json`). Shape:
  `{ "as_of": ISO, "ttl_hours": 20, "symbols": { "RELIANCE.NS": {…features…} } }`.
  Committed by the analyze workflow (`git add data/state`).
- **Raw 2y bars:** fetched, used, **not** committed (no data lake).
- **Dashboard copy:** `public/data/historical_context.json` via `static_exporter`.
- **Tracking over time (4 layers, all existing patterns):**
  1. *Decision-time, append-only (primary):* the features that influenced a
     signal are embedded on its `TradeSignal` and saved to `signal_history.json`;
     never mutated post-outcome.
  2. *Git history:* `data/state` + `public/data` are committed every run →
     diffable evolution.
  3. *Audit:* each refresh appends `{event: "HISTORICAL_CONTEXT_REFRESH", …}`.
  4. *Freshness:* `as_of` drives a ~20h TTL so the 3 daily checkpoints reuse one
     fetch; a new day triggers exactly one refresh.
- **No** separate `historical_context_history.jsonl` (YAGNI — layers 1–2 cover it).

## 8. Pipeline integration

- `storage.load_all_configs()` gains `"context": _load_optional("context.yml")`.
- In `main.py`, **after** the news-risk overlay loop and **before** the paper-buy
  loop (so a context downgrade also prevents a buy), instantiate the engine +
  overlay, refresh (cached), and apply per signal. The engine uses the same
  `provider` already built in `run()`, and calls `usage.record()` on each fetch.
- `static_exporter.export_all()` publishes `historical_context.json` to
  `public/data`.
- The dashboard `Why` view (optional last task) renders one line:
  `vol 88th pctile · near 2y high · β 1.3 · context: elevated volatility`.

## 9. Data models

`TradeSignal` gains (after the news fields, before `created_at`; all defaulted so
serialization and back-compat are automatic via `asdict`/`_to_plain`):

```python
hist_context_available: bool = False
hist_vol_percentile: Optional[float] = None
hist_range_position: Optional[float] = None
hist_pct_above_200dma: Optional[float] = None
hist_beta: Optional[float] = None
hist_context_flags: List[str] = field(default_factory=list)
hist_context_note: str = ""
```

## 10. Error handling & degradation

- yfinance/pandas missing, network failure, or `< min_bars` bars → features
  `None`/`insufficient`; overlay no-ops; signal still produced. Never fatal.
- All feature math is NaN/None-safe and returns `None` rather than raising.
- The whole overlay block in `main.py` is wrapped so it can never break the deep
  run (same discipline as the observation block).
- Deterministic: no randomness, no wall-clock in feature math (the engine passes
  `as_of`; tests inject `now_iso`).

## 11. Testing strategy

Standalone script `scripts/test_historical_context.py` (project pattern: prints
`OK: …`, exits 0), covering:

- **Feature math** on synthetic deterministic series with known vol / SMA /
  drawdown / range / beta / turnover / trend-persistence values.
- **Insufficiency:** `< min_bars` → `coverage="insufficient"`, features `None`.
- **Overlay invariants:** BUY+elevated_vol→WATCH (score unchanged, flag+warning
  present); BUY+thin_liquidity→WATCH; BUY+overextended(flag)→label stays BUY but
  flag attached; non-buy never upgraded; `features=None`→no-op; **score never
  changes** on any path.
- **Engine TTL caching** with a fake provider counting `get_snapshot` calls and
  an injected `now_iso`: first call fetches; second within TTL does not; a call
  past TTL refetches. Uses a throwaway cache filename, cleaned up after.

## 12. Safety invariants (binding)

- ₹0 (yfinance), read-only market data, **caution-only**, deterministic.
- **No** changes to `config/broker.yml`, `config/settings.yml`, or `.github/` —
  the CI safety gate is untouched.
- No new runtime dependencies (uses the existing provider + stdlib math; pandas
  is only touched inside the already-lazy provider).
- Paper-trading only; the overlay can never cause a buy. PR workflow; the user
  merges.

## 13. Future (separate sub-project)

A live backend (Vercel/Render) + database (Mongo or Postgres) migration is
deliberately deferred to its own spec → plan → implementation cycle, to begin
after this feature merges. All disk I/O funnels through `src/storage.py`, so the
later swap is localized. Tracked in memory: `backend-db-migration-plan`.
