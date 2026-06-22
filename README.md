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
