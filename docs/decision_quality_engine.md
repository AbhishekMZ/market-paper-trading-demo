# Decision Quality Engine

> ⚠️ **Paper-trading only — measure, never act.** This layer MEASURES whether the
> system's decisions are actually good. It NEVER auto-tunes thresholds or weights,
> and its readiness verdict NEVER enables real trading. v1 stays paper regardless
> of anything this engine reports.

## Overview & the measure-only invariant

The Decision Quality Engine answers a single question the rest of the system
cannot answer on its own: **are the decisions any good?** Scores, labels, blocks,
and strategy weights are all *inputs* to a decision; this layer watches what
happens *afterwards* and reports it back in plain language.

The invariant is hard, and it is stated in the code itself
(`src/evaluation/decision_quality_engine.py`):

> **This layer only MEASURES. It never changes thresholds or weights, and the
> readiness verdict NEVER enables real trading.**

Every output reflects this. Threshold analysis is explicitly `auto_tuning:
"DISABLED"`. The readiness block always carries `live_trading: "DISABLED"`. The
live buy threshold in `config/scoring.yml` and the strategy weights in
`config/scoring.yml → hybrid_scoring.weights` are never touched by this engine.
Measurement is decoupled from behavior so that *seeing* a result can never, by
construction, *change* a result.

## Why forward returns

A score of 85 means nothing unless 85-scored signals actually tend to rise. You
cannot know that at signal time, so the engine **tracks each symbol forward** and
records the realized price path. This is the measurement spine, and everything
else is built on it.

### The episode model

`forward_return_tracker.py` keeps **one OPEN "episode" per symbol**:

- When a priced signal arrives and the symbol has **no open episode**, it opens
  one, snapshotting the signal's `score`, `label_at_open`, contributing strategies,
  news risk level / `news_blocked` flag, `data_quality_verdict`, and whether the
  signal was **acted on** (`led_to_paper_trade`). The entry price and date are
  recorded.
- Each later run **re-prices the open episode** against its own entry price and
  updates `forward_return_pct` (vs entry), plus running `max_return_pct` and
  `min_return_pct`.
- After `maturity_runs` updates the episode is marked `MATURED` and archived, and
  a fresh episode for that symbol may open. Archived history is bounded per symbol
  (`max_archived_per_symbol`).

### No look-ahead

Every update uses **only the price available on that run** — never a future
price. An episode's forward return at run *N* reflects exactly what a human
watching the same screen at run *N* would have seen. The tracker is pure
persistence plus arithmetic. Ledger: `data/state/forward_returns.json`.

Because forward returns are computed across successive runs, **they need multiple
runs to mature**. A single run produces open episodes with `runs_tracked = 0` and
no meaningful forward return yet.

## Architecture (the `src/evaluation/` module map)

```
src/evaluation/
  forward_return_tracker.py   the spine: opens/advances/matures episodes,
                              records forward_return_pct with no look-ahead
                              (ledger: data/state/forward_returns.json)
  benchmark_comparator.py     appends NIFTY close + portfolio total per run,
                              reports cumulative return vs index + verdict
                              (ledger: data/state/benchmark_history.json)
  shadow_tracker.py           pure: acted vs declined ("shadow") vs blocked
                              forward returns — did our decisions add value?
  strategy_attribution.py     pure: ranks strategies by the avg forward return
                              of every episode they contributed to
  threshold_analysis.py       pure: per candidate threshold, count / hit-rate /
                              avg forward return — DESCRIPTIVE ONLY
  quality_metrics.py          pure aggregate — the headline numbers
  decision_quality_engine.py  orchestrator: runs all of the above, writes
                              decision_quality.json, produces the readiness verdict
```

The two stateful modules (forward-return tracker, benchmark comparator) own a
ledger and are updated + saved each run. The rest are **pure functions** over the
episode list and the benchmark comparison — no state of their own, nothing to
corrupt. The orchestrator composes them.

## What it measures

### Forward returns by score band and acted-vs-declined

`forward_return_tracker.summary()` reports forward-return stats (count, rated,
average return, hit-rate) bucketed by **score band** (`buy_grade` / `watch_grade`
/ `low_grade`, configurable) and split by **acted vs not_acted**. If `buy_grade`
signals do not, on average, outperform `low_grade` ones, the score is not doing
its job — and you can see that directly.

### Shadow & blocked analysis

`shadow_tracker.py` compares the forward returns of:

- **acted** episodes (a paper buy was placed), versus
- **shadow candidates** — strong signals we declined (high WATCH at/above
  `strong_watch_threshold`, or buys blocked by news / data quality), versus
- **blocked** episodes specifically (did blocking actually protect us?).

A protective block shows a **negative** average forward return — the engine
correctly avoided a loser. A costly block shows a **positive** one — a winner was
missed (still paper-safe). The `acted_vs_shadow_edge_pct` quantifies whether
declining was the right call.

### Benchmark vs NIFTY

`benchmark_comparator.py` appends one point per run (NIFTY close + portfolio total
value) to a rolling history, then reports cumulative **portfolio return vs index
return** from the first recorded point, with a verdict of **AHEAD / BEHIND /
INLINE**. A portfolio that lags the index is not adding value, however positive
its P&L looks in isolation.

### Strategy attribution leaderboard

`strategy_attribution.py` ranks each strategy by the **average forward return of
every episode it contributed to**. Because every priced signal opens an episode,
this yields far more samples than the handful of closed trades in a month. It
**complements** the existing `StrategyEvaluator`, which attributes closed-trade
P&L; this one attributes forward returns across all tracked signals.

### Threshold analysis — descriptive only

`threshold_analysis.py` takes each candidate threshold in `thresholds_to_test`,
treats episodes with `score >= T` as "would-buy", and reports `would_buy_count`,
`hit_rate_pct`, and `avg_forward_return_pct`. It even names a
`best_threshold_observed` among thresholds with a real sample.

This is **purely descriptive**. The output carries `auto_tuning: "DISABLED"`. The
live buy threshold in `config/scoring.yml` is never changed automatically — the
table exists so a human can *see* whether the chosen threshold is well placed and
decide for themselves.

## Readiness verdict

`decision_quality_engine._readiness()` produces a plain-language verdict gated on
three maturity checks:

- `enough_trades` — at least `min_trades` filled paper trades,
- `enough_episodes` — at least `min_tracked_episodes` tracked episodes,
- `enough_days` — at least `min_distinct_days` distinct days of benchmark data.

Verdicts:

- **NOT_ENOUGH_DATA** — any gate unmet; reasons spell out exactly what is short
  (e.g. "Only 7/10 paper trades so far").
- **EARLY_PROMISING** — all gates met *and* benchmark outperformance ≥ target
  *and* buy-grade average forward return > 0 *and* decision edge ≥ 0.
- **EARLY_WEAK** — all gates met but the evidence is not yet encouraging.

Crucially, the verdict only describes **how mature the evidence is**. It always
carries:

```
"live_trading": "DISABLED",
"note": "Readiness describes evidence maturity only. v1 stays paper-trading
         regardless of this verdict."
```

Even `EARLY_PROMISING` enables nothing. There is no code path from this verdict to
a real order.

## Configuration (`config/evaluation.yml`)

```yaml
evaluation:
  enabled: true
  forward_returns:
    maturity_runs: 5              # episode matures after this many tracked runs
    max_archived_per_symbol: 10
    open_min_score: 0             # open an episode for any priced signal (0 = all)
    score_bands:                  # [low, high(exclusive), label]
      - [80, 201, "buy_grade"]
      - [65, 80,  "watch_grade"]
      - [0,  65,  "low_grade"]
  shadow:
    track_blocked: true           # treat news/DQ-blocked buys as shadow episodes
    strong_watch_threshold: 65    # WATCH at/above this is a "shadow buy candidate"
  benchmark:
    primary_name: "NIFTY 50"      # matches config/universe.yml benchmarks.primary
    max_history_points: 500
  thresholds_to_test: [70, 75, 80, 85, 90]
  readiness:
    min_trades: 10
    min_tracked_episodes: 20
    min_distinct_days: 20
    target_benchmark_outperformance_pct: 0.0
  disclaimer: >
    Indicative only. One month of paper data cannot prove an edge ...
```

`src/storage.load_all_configs()` loads this file; the engine tolerates being
handed either the whole mapping or just the `evaluation:` block.

## Integration

- `src/main.py` runs `DecisionQualityEngine.evaluate(signals, prices, benchmarks,
  portfolio_summary)` after the portfolio summary each run.
- The engine writes `decision_quality.json` to both `data/reports/` and
  `public/data/`; `src/static_exporter.py` publishes it for the dashboard.
- The dashboard's **Decision Quality** tab renders it: `DecisionQuality` (headline
  + readiness), `BenchmarkComparison`, `StrategyLeaderboard`, `ShadowSignals`,
  and `ThresholdAnalysis`.
- `scripts/reset_demo.py` resets the `forward_returns.json` and
  `benchmark_history.json` ledgers along with the rest of paper state.

## How to generate sample data

A single seed run only opens episodes — forward returns and benchmark history need
**multiple runs to populate**. `scripts/seed_sample_data.py` gained a `--days N`
option that simulates *N* successive runs with price drift through the real
pipeline, so episodes mature and benchmark history accumulates:

```bash
python scripts/seed_sample_data.py --days 6
```

After this you will see matured episodes, populated score-band stats, several
benchmark points, and a non-trivial readiness verdict in the dashboard's Decision
Quality tab. All seeded data is clearly labeled SAMPLE and uses no network.

## Limitations

- **Small sample.** One month of paper data cannot prove an edge. Every output
  says so, in `disclaimer` and in per-section notes.
- **Static synthetic demo prices.** Seeded runs drift prices synthetically; they
  are not real market paths and prove nothing about real performance.
- **Pure-price measure.** Forward return is a keyword-free, price-only signal — it
  knows nothing about *why* a name moved, only that it did.
- **Maturity lag.** Open episodes carry no meaningful forward return until they
  have been advanced across several runs.

## Safety

- **Measure-only.** The engine reads signals, prices, benchmarks, and the
  portfolio summary, and writes a report. It changes no behavior anywhere.
- **No auto-tuning.** Threshold analysis is `auto_tuning: "DISABLED"`; no
  threshold or weight is ever changed automatically.
- **Paper-only.** The readiness verdict always reports `live_trading: "DISABLED"`
  and never enables real trading. There is no path from any verdict to a real
  order. v1 stays paper regardless.
