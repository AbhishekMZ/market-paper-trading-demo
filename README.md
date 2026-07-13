# 📈 Market Paper-Trading Demo (India) — v1: **paper trading only**

A production-minded, **broker-ready** stock analyzer for Indian equities that runs
a **one-month fake-money paper-trading experiment** at **₹0 cost**. It scores a
small universe of large-cap NSE stocks with an explainable **hybrid strategy
engine**, simulates buy/sell/hold decisions through a `PaperBrokerAdapter`,
tracks fake P&L, emails daily reports, and publishes a static dashboard to
GitHub Pages.

It is architected so that switching to **real** Angel One trading later is a
clean, localized, and *safe* change — but **v1 cannot place a real order**.

> ⚠️ **This is a fake-money research/demo project. Not investment advice. No real
> orders are placed in v1.**

---

## 1. What this project does

- Pulls market data for ~10 large-cap NSE stocks at up to 3 daily **checkpoints**
  (09:35 / 11:30 / 14:45 IST) — it does **not** scan continuously.
- Classifies the **market regime** (RISK_ON / NEUTRAL / RISK_OFF / EVENT_RISK /
  DATA_INSUFFICIENT) from NIFTY 50 / NIFTY Bank.
- Scores each stock 0–100 with a **hybrid of modular strategy plugins**
  (trend, relative strength, volatility, news/event risk, portfolio fit, +
  experimental mean-reversion/breakout).
- Generates safe labels (`BUY_SMALL_PAPER`, `WATCH`, `HOLD`, `NO_ACTION`,
  `DO_NOT_BUY`, `HIGH_RISK_IGNORE`, `MANUAL_REVIEW`, `SELL_REVIEW`,
  `TRIM_REVIEW`, `EXIT_REVIEW`).
- Executes **fake** buys/sells only through `PaperBrokerAdapter`, enforcing hard
  risk limits.
- Tracks fake cash, holdings, realized/unrealized P&L, drawdown — **cost-adjusted**.
- Writes daily + end-of-month reports, emails them, and exports JSON for the dashboard.
- Logs **every** decision (and every *no-trade*) with reasoning to an audit log.

## CLI control

Most local operations can be run without an LLM through the repo CLI:

```powershell
py -3 mmg.py status
py -3 mmg.py profile apply max-paper
py -3 mmg.py analyze --checkpoint close --force
py -3 mmg.py execute --checkpoint close --force
```

See [`docs/CLI.md`](docs/CLI.md) for profiles, config edits, history inspection,
and timeout options.

## 2. What it does **not** do in v1

- ❌ No real orders. ❌ No Angel One credentials. ❌ No live broker execution.
- ❌ No intraday / margin / F&O / options / short selling / market orders.
- ❌ No WhatsApp / Telegram (email only). ❌ No paid services. ❌ No database.
- ❌ No machine learning, no automatic strategy optimization.

## 3. Why v1 is ₹0 cost

Everything runs on free tiers: **GitHub public repo + GitHub Actions + GitHub
Pages**, market data via the free **Yahoo Finance** library (`yfinance`, no API
key), **Gmail SMTP** for email, and plain **JSON/YAML** files for storage. No
servers, no databases, no paid APIs.

---

## 4. How the architecture is broker-ready

The whole system talks to one interface — `BrokerAdapter` — never to a concrete
broker. Strategy/risk/execution logic is completely separate from execution
mechanics, so moving to a real broker is a localized adapter swap.

```
signal/strategy engine ─┐
risk engine ────────────┼──► ExecutionEngine ──► BrokerAdapter (interface)
execution mode/flags ───┘                         ├── PaperBrokerAdapter   (ENABLED, v1)
                                                  └── AngelOneBrokerAdapter (DISABLED stub)
```

Market data is *also* abstracted, so the data source is swappable too:

```
MarketDataProvider (interface)
  ├── YahooFinanceProvider  (ENABLED, v1 — yfinance)
  ├── YahooQueryProvider    (future option, skeleton)
  └── SerpApiProvider       (disabled)
```

### 5. How `BrokerAdapter` works
`src/broker/base.py` defines: `get_account_profile`, `get_cash_balance`,
`get_holdings`, `get_positions`, `get_ltp`, `place_order`, `modify_order`,
`cancel_order`, `get_order_status`, `get_order_book`, `get_trade_book`.
**No strategy logic lives in adapters** — they only execute and report.

### 6. Why `PaperBrokerAdapter` is the only enabled adapter in v1
It fully simulates equity-delivery paper trades against JSON state, needs no
credentials, marks every order `is_paper=true`, and enforces risk rules as a
backstop. It is the *only* adapter `ExecutionEngine` will run in v1.

### 7. How `AngelOneBrokerAdapter` can be added later
`src/broker/angel_one_stub.py` is a disabled skeleton: every live method raises
`DisabledBrokerError`, it performs no network calls, asks for no credentials, and
has `TODO`s marking exactly where SmartAPI auth/order placement would go. See
[`docs/future_real_trading_transition.md`](docs/future_real_trading_transition.md).

### 8. Why live trading is disabled by default
`ExecutionEngine.validate_safety()` **refuses to run** if any unsafe combination
is present (live enabled but adapter still paper; angel_one selected but not
enabled/confirmed; real orders allowed; any non-paper adapter in v1; disallowed
order types). The GitHub Action also runs a safety gate before the analyzer.

---

## 9. Hybrid algorithm design

The strategy layer is **modular plugins**, not one monolith (`src/strategy/`):

- `market_regime.py` — `MarketRegimeEngine` classifies the market and **gates** buys.
- `trend_following.py`, `relative_strength.py`, `volatility_risk.py`,
  `news_event_risk.py`, `portfolio_fit.py` — **core** contributing strategies.
- `mean_reversion.py`, `breakout.py` — **experimental**, display-only in v1.
- `hybrid_signal_engine.py` — runs all plugins, combines them into one
  explainable 0–100 score, applies penalties, detects **conflicts** (prefers
  `NO_ACTION` when strategies disagree), and applies **regime gating**.
- `strategy_evaluator.py` — attributes outcomes back to strategies.
- `research_registry.py` — treats each strategy as a **hypothesis**.

Default v1 weights (`config/scoring.yml → hybrid_scoring.weights`, sum 100):
trend 20, relative strength 20, market regime 20, volatility 15, news/event 15,
portfolio fit 10, mean-reversion 0 (experimental), breakout 0 (experimental).

**Final score** = weighted blend of contributing strategies + the regime score,
minus transparent risk penalties — fully explainable per symbol.

### How strategy plugins work
Each plugin implements `StrategyPlugin` (`name/describe/required_fields/evaluate/
explain`) and returns a `StrategyResult` (score_contribution, confidence, signal,
reason, data_used, warnings, risk_flags, is_valid…). **Strategies never trade** —
they only produce evidence and a score contribution.

### How to add a new strategy
1. Create `src/strategy/<your_strategy>.py` implementing `StrategyPlugin`.
2. Register it in `hybrid_signal_engine.PLUGIN_CLASSES`.
3. Give it a weight in `config/scoring.yml → hybrid_scoring.weights` (start at 0
   = display-only) and add a hypothesis to `config/research_hypotheses.yml` with
   `validation_status: untested`.
4. Validate on paper for a month before raising its weight.

### How to disable/enable a strategy
Set its weight to `0` (display-only) or list it under
`experimental_strategies: { <name>: { contributes_to_score: false } }` in
`config/scoring.yml`. Experimental strategies are shown but cannot trigger buys.

### How market regime affects buy decisions
- **RISK_ON** → buys allowed if the stock score qualifies.
- **NEUTRAL** → buys need higher confidence; weak ones are downgraded to WATCH.
- **RISK_OFF** → fresh buys **blocked**; open positions reviewed.
- **EVENT_RISK** → buy candidates become `MANUAL_REVIEW`.
- **DATA_INSUFFICIENT** → no new buys.

### Why v1 avoids ML & treats strategies as hypotheses
See [`docs/strategy_validation_principles.md`](docs/strategy_validation_principles.md).
Short version: explainability and overfitting-avoidance matter more than
sophistication when you're deciding whether a simple edge is even real.

### How cost-adjusted paper P&L is calculated
`src/backtesting/cost_model.py` estimates Indian **delivery** costs (STT,
exchange charges, GST, stamp duty, slippage, half-spread) per side and round-trip
(`config/costs.yml`, all configurable). Reports show gross **and** net-of-cost P&L
so the demo doesn't look unrealistically good.

---

## 10. Market data: Yahoo Finance via `yfinance`

v1 uses **Yahoo Finance** through the **`yfinance`** library.

> ⚠️ **`yfinance` is UNOFFICIAL** — not affiliated with, endorsed, or vetted by
> Yahoo. It uses Yahoo's publicly available endpoints and is intended for
> research / educational / paper-trading use. Do **not** treat it as a guaranteed
> production feed. (`yahooquery` is another unofficial option for later.)

- **NSE symbols:** `SYMBOL.NS` (e.g. `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`).
- **BSE symbols:** `SYMBOL.BO` (configure manually if needed).
- **Indices:** NIFTY 50 = `^NSEI`, NIFTY Bank = `^NSEBANK`.
- **No API key, no quota** — but the run stays polite (`rate_limits` in
  `config/settings.yml`) and caps symbols per run.

### Switching providers later
Set `market_data.provider` in `config/settings.yml` (e.g. to `yahooquery` once
implemented) and/or add a new provider under `src/market_data/`. Strategies are
unaffected — they only see the normalized `MarketSnapshot`.

### Data-quality & anomaly handling (important)
Unofficial feeds occasionally return bad, stale, or **adjusted/unadjusted**
prices. Acted on blindly, that produces misleading paper trades and P&L (e.g. a
position entered on one price basis and marked on another can show a fake −40%).
`src/data_quality/` (`DataQualityEngine`) guards against this:

- **Before trusting a quote**, it checks current price vs the latest history
  close (basis mismatch), price-within-recent-range, staleness, extreme moves
  with no news, and split/corporate-action discontinuities. A failure ⇒ verdict
  `DATA_ANOMALY`, the symbol is **excluded from pricing**, and **buys are blocked**
  (label forced to `NO_ACTION`). The execution engine also blocks such buys as
  defense-in-depth.
- **Marking held positions**, a new mark that jumps more than
  `data_quality.mtm_jump_pct` vs the last-known-good price is **rejected** — the
  prior price is kept, the position is flagged `DATA_ANOMALY`, and an incident is
  recorded (never a fake loss).
- Every signal stores `price_source`, `entry_price_used`, `mtm_price_used`,
  `price_consistency_check`, and `data_quality_verdict`.
- Incidents → `data/reports/data_quality_incidents.json` (+ public, capped);
  a per-run **Data Health** snapshot → `data_health.json` (shown on the dashboard's
  Data Health tab). Tune thresholds in `config/settings.yml → data_quality`.

**Reset the demo:** if state ever gets corrupted, run
`python scripts/reset_demo.py --confirm RESET_PAPER_DEMO` (or the **reset-demo**
GitHub Action with input `RESET_PAPER_DEMO`) to wipe paper state to a clean start.

### News risk layer (important)
A **post-strategy risk overlay** (`src/news/`) that runs *after* the hybrid
scoring engine, per symbol, and can **only add caution**. The cardinal rule is
enforced in code (`news_risk_engine.apply_to_signal`): adverse news may
**block or downgrade** a paper buy, but **news can never create or upgrade a
buy**. Positive news is recorded as a mild informational `sentiment_boost` only —
it is not added to the score and can never cross the buy threshold, so **news
alone can never trigger a buy.**

- **Providers (₹0-cost):** `yfinance` headlines already fetched with the price
  snapshot (no extra call), plus the free, key-less **GDELT** 2.0 Doc API (8 s
  timeout, cached, degrades to "no news" on any failure). `NewsAPI` is **disabled**
  (needs a key). Sentiment + event classification are keyword-driven, deterministic,
  and tunable in `config/news.yml` — no ML.
- **Verdict → action:** `CRITICAL`/`HIGH` adverse news **blocks** a fresh buy
  (`CRITICAL` → `NO_ACTION`, `HIGH` → `WATCH`); `MEDIUM` → `MANUAL_REVIEW`;
  `CRITICAL` news on a held position flags `EXIT_REVIEW` (advisory — v1 never
  auto-sells). `src/execution_engine.py` independently re-blocks any buy with
  `news_blocks_buy` set (audit event `PAPER_BUY_BLOCKED_BY_NEWS`) as defense-in-depth.
- **Alerts:** email only (Gmail SMTP), on `CRITICAL` news (watched/held), `HIGH`
  news on a held position, or `HIGH` news that blocked a buy. Throttled to
  `max_alerts_per_run` (default 5); every body reminds **PAPER TRADING ONLY**.

Full design, pipeline, and config reference: [`docs/news_risk_layer.md`](docs/news_risk_layer.md).

### Decision Quality Engine (important)
A **measure-only evaluation layer** (`src/evaluation/`) that runs after the
portfolio summary each run and asks one question: *are the system's decisions
actually good?* The invariant is enforced in code: it **only measures** — it
**never** auto-tunes thresholds or weights, and its verdict **never enables real
trading**. v1 stays paper regardless.

- **Forward-return episodes** (`forward_return_tracker.py`) are the spine: each
  priced signal opens one episode per symbol (snapshotting score, label,
  contributors, news/DQ flags, and whether it was acted on); later runs re-price
  it and record `forward_return_pct` vs entry, maturing after `maturity_runs`.
  **No look-ahead** — each update uses only that run's price. A score is only
  meaningful if high-score signals actually rise, and this is how we check.
  Ledger: `data/state/forward_returns.json`.
- **Shadow / benchmark / attribution / threshold** analyses sit on top: acted vs
  declined ("shadow") vs blocked forward returns (a protective block shows a
  *negative* avg return); cumulative portfolio return **vs NIFTY** with an
  AHEAD/BEHIND/INLINE verdict; a strategy leaderboard ranked by the forward
  return of every episode a strategy contributed to; and a **descriptive** per-
  threshold table (`auto_tuning: "DISABLED"` — the live buy threshold in
  `config/scoring.yml` is never changed automatically).
- **Readiness verdict** (`NOT_ENOUGH_DATA` / `EARLY_PROMISING` / `EARLY_WEAK`) is
  gated on min trades / episodes / distinct days, describes only how mature the
  evidence is, and always reports `live_trading: "DISABLED"` — it never enables
  live trading. One month of paper data cannot prove an edge; every output says so.
- **Seeding tip:** forward returns and benchmark history need multiple runs to
  populate, so simulate successive runs with price drift via
  `python scripts/seed_sample_data.py --days 6`.

Config keys live in `config/evaluation.yml`; the engine publishes
`decision_quality.json` to the dashboard's **Decision Quality** tab. Full design
reference: [`docs/decision_quality_engine.md`](docs/decision_quality_engine.md).

### Observation & Escalation Engine (important)
A **lightweight, between-checkpoint monitoring layer** (`src/observation/`) that
watches a **small active watchlist** (≤ ~15 symbols — open positions + a handful
of live buy candidates, **not** the full universe) more frequently than the three
fixed deep-analysis checkpoints (09:35 / 11:30 / 14:45 IST). Why: the deep view
**goes stale between checkpoints**, so a breakout or a headline at 12:10 wouldn't
be looked at until 14:45. The observer re-prices just that short list, runs
deterministic trigger rules, and reacts — **no full-universe scan, no new daily
signals.**

- **Triggers it watches:** price breakout / breakdown / large-move-since-last /
  gap; held-position soft/strong/hard-loss + profit reviews; HIGH/CRITICAL news;
  market-regime shifts (→ RISK_OFF / EVENT_RISK / DATA_INSUFFICIENT); and
  data-quality anomalies / stale quotes / provider failures (which **block
  action**).
- **"Swift action" = swift PAPER action or a manual-review alert — never a real
  order.** A breakout on a buy candidate triggers **focused re-analysis** (the
  *same* hybrid scoring + data-quality gate + news overlay, for one symbol); only
  if it still qualifies **and** every gate passes does it place a swift **paper**
  buy — and **only** through `ExecutionEngine.process_buy` (which independently
  enforces risk + data-quality + news + daily/monthly limits + LIMIT + DELIVERY +
  paper-only). **Sell is review-only; the observer never auto-sells.** Cooldowns +
  per-run caps keep it low-noise; cumulative metrics feed the Decision Quality
  Engine so the system measures whether observation added value or just noise.
- **CLI:** `--observe` (deep run, then observe once), `--observe-only` (watchlist
  + positions only, no scan/new signals), `--focused-symbol RELIANCE.NS`,
  `--escalation-report`, `--no-action` (never create even a paper order).
- **GitHub Actions:** `analyze.yml` gained `workflow_dispatch` inputs
  `observe_only` / `focused_symbol` / `no_action`; a separate **`observe.yml`**
  runs `--observe-only` (manual-dispatch by default; schedule examples commented
  out). **GitHub Actions is NOT a real-time engine** (cron jitter, no intraday
  guarantees) — v1 stays manual + low-noise on purpose.

Full design: [`docs/observation_escalation_engine.md`](docs/observation_escalation_engine.md).
Future lower-latency / gated-live phases:
[`docs/future_realtime_execution.md`](docs/future_realtime_execution.md).

---

## 11. Setup

### Prerequisites
- Python 3.11, Node 20 (for the frontend), a GitHub account, a Gmail account.

### Local install
```bash
pip install -r requirements.txt
cp .env.example .env     # fill in Gmail values; market data needs no key
```

### Create a Gmail App Password (for email alerts)
1. Enable 2-Step Verification on your Google account.
2. Google Account → Security → **App passwords** → generate one for "Mail".
3. Put the 16-digit value in `.env` as `GMAIL_APP_PASSWORD` (and your address as
   `GMAIL_USER`). Set `ALERT_EMAIL_TO=sahabhi115@gmail.com`.

### Add GitHub Actions secrets
Repo → Settings → Secrets and variables → Actions → **New repository secret**:
- `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL_TO`.
- **No `SERPAPI_KEY` and no Angel One secrets are required in v1.**

---

## 12. Running it

```bash
# From the repo root:
python src/main.py --manual --checkpoint close   # one-off run now
python src/main.py --checkpoint auto             # infer checkpoint from IST time
python src/main.py --eod                          # treat as end-of-day (emails report)
python src/main.py --monthly                      # also write the month report

# Generate clearly-labeled SAMPLE data (no network) for the dashboard:
python scripts/seed_sample_data.py

# Sanity-check the live Yahoo provider (needs internet):
python scripts/test_yfinance_provider.py
```

### Run the frontend locally
```bash
cd frontend
npm install
npm run dev        # opens a local dev server; reads ../public/data via a prebuild copy
npm run build      # outputs frontend/dist for GitHub Pages
```

---

## 13. Deploy to GitHub Pages (₹0)

1. Push this project to a **public** GitHub repo.
2. Repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Add the Gmail secrets (above).
4. The **`deploy-pages`** workflow builds `frontend/` and publishes the dashboard;
   the **`analyze`** workflow updates the data it reads.

### Enable scheduled analysis
The `analyze` workflow already has weekday cron triggers (UTC) for the three IST
checkpoints, plus manual `workflow_dispatch`. After the first manual run + Pages
enablement, it runs automatically on weekdays.
- 09:35 IST = `5 4 * * 1-5`, 11:30 IST = `0 6 * * 1-5`, 14:45 IST = `15 9 * * 1-5`.

### Keeping data usage polite
`yfinance` has no key/quota, but keep `market_data.max_symbols_per_run` small
(8–10), use ≤ 3 checkpoints/day (or set `single_checkpoint_mode: true`), and the
built-in `rate_limits` add polite sleeps + retries.

---

## 14. Running the one-month paper demo & reading results

- Let the scheduled workflow run on weekdays for ~a month. Each run updates
  `data/state/*`, `data/reports/*`, and `public/data/*` (committed back), and the
  dashboard refreshes.
- **Reading fake P&L:** the dashboard's Portfolio/Dashboard views show fake cash,
  holdings, realized + unrealized P&L, return %, drawdown, and the **cost-adjusted**
  net. Everything is fake money.
- **End-of-month:** run with `--monthly` (or dispatch with `monthly=true`) to get
  `data/reports/monthly_<YYYY-MM>.{json,md}`.

### Evaluation metrics after one month
Number of paper trades, win rate, average gain/loss, max drawdown, best/worst
trade, false positives, avoided bad trades, monthly fake return, **vs NIFTY 50**,
data-quality skips, no-trade count, risk-rejection count, per-strategy
contribution analysis, and a manual-approval **readiness** verdict. See the
StrategyEvaluation view and the monthly report. **Do not over-trust one month.**

---

## 15. Real Angel One trading later — and why it's disabled now

Real broker execution is intentionally **disabled** in v1 because an unvalidated
strategy placing real orders is how people lose money. The transition path,
required safety checks, the strategy-eligibility gate, and the note that real
execution may need a static IP / non–GitHub-Actions deployment are all in
[`docs/future_real_trading_transition.md`](docs/future_real_trading_transition.md).
Regulatory/safety considerations for retail algo trading in India are summarized
there and in the validation-principles doc.

---

## Project layout
```
config/      settings.yml, universe.yml, scoring.yml, broker.yml, risk.yml, costs.yml, research_hypotheses.yml
src/         main.py, execution_engine.py, risk_engine.py, portfolio_manager.py, report_generator.py,
             email_sender.py, static_exporter.py, scheduler.py, storage.py, utils.py, order_models.py
src/broker/      base.py, paper_broker.py, angel_one_stub.py
src/market_data/ base.py, yahoo_finance_provider.py, yahooquery_provider.py, serpapi_provider.py, provider_factory.py
src/strategy/    base, market_regime, trend_following, relative_strength, mean_reversion, breakout,
                 news_event_risk, volatility_risk, portfolio_fit, hybrid_signal_engine, strategy_evaluator, research_registry
src/backtesting/ cost_model.py, backtest_engine.py, walk_forward_validator.py
data/        raw/ processed/ reports/ state/   (JSON/JSONL state + reports)
public/data/ JSON the dashboard reads
frontend/    React + Vite dashboard
docs/        future_real_trading_transition.md, strategy_validation_principles.md
.github/workflows/ analyze.yml, deploy-pages.yml
```

## Disclaimer
Fake-money educational/research demo for Indian equities. **Not investment
advice.** Market data via `yfinance` is unofficial. Past (paper) performance does
not indicate future results. You are responsible for any real-trading decisions
you later make.
