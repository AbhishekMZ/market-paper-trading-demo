# Observation & Escalation Engine

> ⚠️ **PAPER TRADING ONLY (v1).** The observer **never places a real order**,
> **never auto-sells**, and **never bypasses** the Risk / News / DataQuality /
> ExecutionEngine gates. "Swift action" means a **swift paper buy** (through the
> same `ExecutionEngine.process_buy` as the deep pipeline) **or** a manual-review
> email alert — *never* a live order. No Angel One. No market orders. No
> intraday / F&O / margin / short.

---

## Overview — the product problem it solves

The deep-analysis pipeline runs at three fixed **checkpoints** (09:35 / 11:30 /
14:45 IST). That is deliberate (₹0-cost, low-noise, `yfinance`-polite) — but it
means the system's view of the world **goes stale between checkpoints**. A buy
candidate that was one news headline or one breakout away at 11:30 can move
meaningfully at 12:10, and the next deep run won't look until 14:45.

The **Observation & Escalation Engine** (`src/observation/`) closes that gap
*without* turning the demo into a continuous trading bot. It:

1. builds a **small active watchlist** (≤ ~15 symbols) of what actually matters
   right now — open positions + a handful of live buy candidates — **not** the
   full universe;
2. re-prices just those symbols more frequently and runs **deterministic trigger
   rules** to detect *meaningful change*;
3. **escalates** the significant triggers (severity-first, throttled);
4. runs **focused re-analysis** for an affected symbol using the *same* engines
   the deep pipeline uses; and
5. takes **swift PAPER action** (only if every gate passes) **or** raises a
   **manual-review alert**.

It is intentionally lightweight: **no full-universe scan, no new daily signals,
no continuous polling.** It watches a short list and reacts to it.

## Deep analysis vs observation

| Aspect | Deep analysis (`--manual` / scheduled) | Observation (`--observe` / `--observe-only`) |
| --- | --- | --- |
| Scope | Full configured universe (~10 stocks) | Small active watchlist + open positions (≤ ~15) |
| Cadence | 3 fixed IST checkpoints | Between checkpoints (target 30–60 min; manual-dispatch in v1) |
| Generates new daily signals? | **Yes** | **No** — reacts to existing state only |
| Cost / weight | Heavier (whole universe, full scoring) | Lightweight (re-price a short list) |
| Scoring engine | Hybrid plugins + regime + risk penalties | **Same** engines, re-run for one symbol (focused) |
| Can take a paper buy? | Yes, via `ExecutionEngine` | Yes, via the **same** `ExecutionEngine` — after focused re-analysis + all gates |
| Can sell? | `SELL/TRIM/EXIT_REVIEW` (advisory) | `SELL/TRIM/EXIT_REVIEW` (advisory) — **review-only, never auto-sells** |
| Purpose | "What is the full picture right now?" | "Did anything important change since the last checkpoint?" |

Observation **reuses the deep stack's gates** — it must never run on a weaker or
parallel set of rules. The `ObservationEngine` constructs the *same*
`HybridSignalEngine`, `NewsRiskEngine`, and `DataQualityEngine` the deep pipeline
uses.

## Architecture — the `src/observation/` module map

```
src/observation/
├── trigger_models.py     Enums (TriggerType / TriggerSeverity / TriggerStatus /
│                         ActionType) + dataclasses TriggerEvent / EscalationItem /
│                         ObservationResult. The shared contracts.
├── trigger_rules.py      TriggerRules — deterministic, explainable change detection.
│                         Pure rules, no side effects; emits TriggerEvents.
├── watchlist_manager.py  WatchlistManager — builds the small ACTIVE watchlist
│                         (deduped by symbol, best priority wins, capped).
├── observation_state.py  ObservationState — per-symbol last-seen memory
│                         (last price / regime / news risk / DQ verdict) for diffing.
├── cooldown_manager.py   CooldownManager — same-symbol / same-trigger / paper-buy
│                         cooldowns (cross-run; data/state/alert_cooldowns.json).
├── alert_throttle.py     AlertThrottle — per-run caps on escalations + emails,
│                         in-run duplicate-email suppression.
├── focused_analysis.py   FocusedAnalysis — re-runs the SAME hybrid scoring +
│                         data-quality gate + news overlay for ONE symbol.
├── escalation_engine.py  EscalationEngine — decides the action, emails, and is the
│                         ONLY path to a paper buy (via ExecutionEngine.process_buy).
└── observation_engine.py ObservationEngine — orchestrator: build watchlist →
                          re-price → trigger rules → escalation → persist/export.
```

## Data flow

```
            ┌──────────────────────────┐
            │  WatchlistManager.build  │  open positions + buy candidates + WATCH
            │  (≤ ~15, deduped, capped)│  + improving rejections + shadow + pinned
            └────────────┬─────────────┘
                         │  active_watchlist.json
                         ▼
            ┌──────────────────────────┐
            │  Lightweight re-fetch     │  yfinance snapshot per watched symbol
            │  (price + headlines)      │  (NO full-universe scan)
            └────────────┬─────────────┘
                         ▼
   ObservationState  ┌──────────────────────────┐   DataQualityEngine
   (last-seen) ─────▶│      TriggerRules         │◀── + NewsRiskEngine + regime
                     │  deterministic detection  │
                     └────────────┬─────────────┘
                         triggers │  (severity-first)
                                  ▼
            ┌──────────────────────────────────────┐
            │           EscalationEngine            │
            │  cooldowns + per-run throttle applied  │
            └───┬───────────────┬──────────────┬────┘
                │ buy candidate  │ data/news/   │ held-position
                │ breakout/move  │ regime block │ loss/profit
                ▼                ▼              ▼
        FocusedAnalysis   BLOCKED_BY_*    SELL/TRIM/EXIT_REVIEW
        (same engines)    (no action)     (advisory, never auto-sells)
                │
       all gates pass? ──no──▶ PAPER_BUY_REVIEW / MANUAL_REVIEW / OBSERVE_ONLY
                │yes
                ▼
   ExecutionEngine.process_buy  ──▶  SWIFT PAPER BUY (the ONLY path to a trade)
        (risk + DQ + news + daily/monthly limits + LIMIT + DELIVERY + paper-only)
                │
                ▼
        Email alert (throttled) + reports/exports + observation_metrics.json
```

## Trigger types

Triggers are emitted by `trigger_rules.py` as `TriggerEvent`s, grouped below.
Triggers flagged **(blocks action)** force a no-buy verdict — bad data or adverse
news can never become a buy.

**Price (watchlist + positions)**
- `PRICE_BREAKOUT` — price broke above the recent high (a buy candidate breaking
  out is the main path to a swift paper buy; sets `requires_focused_analysis`).
- `PRICE_BREAKDOWN` — price broke below the recent low (caution; review if held).
- `LARGE_MOVE` — moved ≥ `intraday_move_alert_pct` (default 3%) **since the last
  observation** (escalates HIGH at ≥ 2× the threshold).
- `GAP_MOVE` — moved ≥ `gap_alert_pct` (default 2.5%) **vs the previous close**.

**Position (held only)**
- `SOFT_LOSS_REVIEW` (≤ −7%) → `SELL_REVIEW`
- `STRONG_LOSS_REVIEW` (≤ −10%) → `TRIM_REVIEW`
- `HARD_LOSS_REVIEW` (≤ −15%) → `EXIT_REVIEW`
- `PROFIT_REVIEW` (≥ +8%) → `TRIM_REVIEW`
  All are **advisory** — v1 **never auto-sells**.

**News**
- `HIGH_RISK_NEWS` — **(blocks action)**; blocks a fresh buy, review if held.
- `CRITICAL_NEWS` — **(blocks action)**; `EXIT_REVIEW` if held, else block.

**Regime** (market-wide, emitted once)
- `MARKET_REGIME_SHIFT` — **(blocks action)** on `RISK_ON/NEUTRAL → RISK_OFF`,
  `→ EVENT_RISK`, or `→ DATA_INSUFFICIENT`; blocks new buys + manual review.

**Data quality** (evaluated first; short-circuits price triggers on the symbol)
- `DATA_ANOMALY` — **(blocks action)** price anomaly; symbol not trusted.
- `STALE_QUOTE` — **(blocks action)** stale quote; await fresh data.
- `PROVIDER_FAILURE` — **(blocks action)** no usable quote / `DATA_INSUFFICIENT`.

## Escalation rules — trigger → action mapping

The `EscalationEngine` picks the **dominant** (highest-severity) trigger per
symbol, then maps it to an `ActionType`:

| Situation | Resulting action |
| --- | --- |
| Data anomaly / stale quote / provider failure | `BLOCKED_BY_DATA_QUALITY` (no action) |
| HIGH/CRITICAL news on a **buy candidate** | `BLOCKED_BY_NEWS` |
| CRITICAL news on a **holding** | `EXIT_REVIEW` (advisory; never auto-sells) |
| HIGH news on a **holding** | `SELL_REVIEW` (advisory) |
| Regime → RISK_OFF / EVENT_RISK / DATA_INSUFFICIENT | `MANUAL_REVIEW` (new buys blocked) |
| Held position soft / strong / hard loss | `SELL_REVIEW` / `TRIM_REVIEW` / `EXIT_REVIEW` (advisory) |
| Held position profit review | `TRIM_REVIEW` (advisory) |
| Breakout / large up-move on a **buy candidate** → focused re-analysis qualifies, all gates pass, not on cooldown, not `--no-action` | `PAPER_BUY_ALLOWED` (swift paper buy via `ExecutionEngine`) |
| …qualifies but on paper-buy cooldown or `--no-action`/config-suppressed | `PAPER_BUY_REVIEW` |
| …focused re-analysis blocked by news / data quality | `BLOCKED_BY_NEWS` / `BLOCKED_BY_DATA_QUALITY` |
| …focused re-analysis returns `MANUAL_REVIEW` | `MANUAL_REVIEW` |
| …focused re-analysis qualifies on score but a risk/limit gate rejects at execution | `BLOCKED_BY_RISK` |
| …focused re-analysis no longer a buy | `OBSERVE_ONLY` |
| Everything else (informational) | `OBSERVE_ONLY` |

## Action readiness rules

A swift **paper buy** is the *only* action the observer can take autonomously,
and it requires **all** of the following — every one enforced in code, not just
documented (`escalation_engine._decide` / `_try_paper_buy` →
`focused_analysis.analyze`):

1. The trigger is a **breakout / up-move on a buy candidate** (not held), which
   set `requires_focused_analysis`.
2. **Focused re-analysis** (`FocusedAnalysis`) re-runs the **same** hybrid
   scoring engine for that single symbol and the label is still
   `BUY_SMALL_PAPER` (`action_allowed`).
3. The **data-quality gate** passes (`verdict == "OK"`; otherwise the buy label
   is forced to `NO_ACTION` and it is `BLOCKED_BY_DATA_QUALITY`).
4. The **news overlay** does not block (no `news_blocks_buy`; news can only add
   caution, never create or upgrade a buy).
5. The result is not `MANUAL_REVIEW`.
6. The symbol is **not on paper-buy cooldown** (`paper_trade_cooldown_after_buy_hours`).
7. The run is **not** in `--no-action` mode and paper buys are allowed in config
   (`allow_paper_buy_after_trigger: true`).
8. **And then** the buy is placed *only* through
   `ExecutionEngine.process_buy(...)`, which **independently** enforces risk
   limits + data-quality + news + daily/monthly buy limits + **LIMIT** order +
   **DELIVERY** + **paper-only**, capped at `max_trade_amount`. If any of these
   reject it, the action becomes `BLOCKED_BY_RISK` and no order is created.

There is **no other code path** from the observer to a trade. SELL/TRIM/EXIT are
review-only — the observer cannot place a sell at all in v1.

## Cooldowns & throttling

Driven by `config/observation.yml → observation.cooldowns` + `…escalation`:

- **`same_symbol_alert_cooldown_minutes`** (120) — suppress repeat alerts on the
  same symbol.
- **`same_trigger_alert_cooldown_minutes`** (180) — suppress the same
  (symbol, trigger) within the window; a symbol on cooldown is skipped this run.
- **`paper_trade_cooldown_after_buy_hours`** (24) — no second swift paper buy on
  a symbol within the window (→ `PAPER_BUY_REVIEW` instead).
- **`escalation_expiry_hours`** (24) — escalation items age out.
- **`max_escalations_per_run`** (5) — only the most urgent symbols get the
  limited escalation slots (severity-first ordering).
- **`max_email_alerts_per_run`** (5) — bounds emails per run; **duplicate email
  keys within a run are suppressed**.

Cross-run cooldowns persist to `data/state/alert_cooldowns.json`; per-run caps
are in-memory (`AlertThrottle`). The escalation queue is **rolling**, so a later
cooldown-throttled run never wipes earlier escalations.

## CLI usage

```bash
# 1) Deep analysis, then observe the watchlist + positions ONCE (default scheduled run)
python src/main.py --observe

# 2) ONLY observe — no full universe scan, no new daily signals
python src/main.py --observe-only

# 3) Observe a single symbol (focused re-analysis path)
python src/main.py --observe-only --focused-symbol RELIANCE.NS

# 4) Regenerate the escalation report from the current queue and exit (no scan)
python src/main.py --escalation-report

# 5) Analyze / observe only — NEVER create even a paper order
python src/main.py --observe-only --no-action
```

- **`--observe`** — run deep analysis, then observe once.
- **`--observe-only`** — skip the heavy scan; observe watchlist + positions only.
- **`--focused-symbol SYMBOL`** — restrict observation to one symbol.
- **`--escalation-report`** — light path; rewrite the report from the persisted
  queue, no fetch.
- **`--no-action`** — observe/analyze only; **no paper order is ever created**.

## GitHub Actions limitations

> ⚠️ **GitHub Actions is NOT a precision real-time engine.** Cron has jitter,
> there are no intraday execution guarantees, and runners are ephemeral. v1
> deliberately stays **manual-dispatch + low-noise**.

- **`analyze.yml`** gained `workflow_dispatch` inputs: **`observe_only`**,
  **`focused_symbol`**, and **`no_action`** so a manual run can observe (or
  observe one symbol, or analyze without acting).
- **`observe.yml`** is a separate workflow that runs `--observe-only`. It is
  **`workflow_dispatch` by default**; example schedule entries are **commented
  out** on purpose. Enable a schedule only when you accept the noise/jitter
  trade-offs.
- Why low-noise: the engine exists to add *signal*, not alert spam. The cooldowns
  + per-run caps, the small watchlist, and manual dispatch all keep the demo
  cheap and trustworthy. Lower-latency, always-on monitoring is a **later phase**
  — see `docs/future_realtime_execution.md`.

## Decision Quality integration

Every run updates cumulative `data/state/observation_metrics.json`
(`observation_runs`, `triggers_detected`, `escalations_created`,
`paper_actions_from_triggers`, `blocked_actions_from_triggers`, …). The Decision
Quality Engine summarizes this into `decision_quality.json` under an
**`observation`** block — `observation_runs`, `triggers_detected`,
`escalations_created`, `paper_actions_from_triggers`,
`blocked_actions_from_triggers`, `useful_triggers`, and an `alert_noise_score`.

This lets the system **measure whether observation added value or just noise** —
consistent with the rest of the project: the layer is held to evidence, not
assumed useful.

## Storage & exports

- **State** (`data/state/`): `observation_state.json`, `active_watchlist.json`,
  `trigger_history.json`, `escalation_queue.json`, `alert_cooldowns.json`,
  `observation_metrics.json`.
- **Reports** (`data/reports/`): `observation_report.json` / `.md`,
  `escalation_report.json` / `.md`.
- **Public exports** (`public/data/`, dashboard-read): `observation_report.json`,
  `escalation_report.json`, `active_watchlist.json`,
  `trigger_history.json` (cap 300, newest first),
  `escalation_queue.json` (cap 100, newest first), `observation_state.json`.
- **Dashboard "Observation" tab:** `ObservationPanel`, `ActiveWatchlist`,
  `TriggerHistory`, `EscalationQueue`, `ActionReadiness`.

## Safety — the hard invariants

These are **enforced in code**, not merely promised:

- The observer **NEVER places a real order.** Any swift paper buy flows **only**
  through `ExecutionEngine.process_buy`, which independently enforces risk +
  data-quality + news + daily/monthly limits + **LIMIT** + **DELIVERY** +
  **paper-only**. There is no other path to a trade.
- The observer **NEVER auto-sells.** Sell is **review-only** in v1
  (`SELL_REVIEW` / `TRIM_REVIEW` / `EXIT_REVIEW` are advisory;
  `allow_paper_sell_after_trigger: false`).
- The observer **NEVER bypasses** Risk / News / DataQuality / ExecutionEngine —
  it reuses the **same** engines as the deep pipeline.
- **Bad data or adverse news can never become a buy.** Data-quality is checked
  first and short-circuits price triggers; news can only add caution.
- **No Angel One, no market orders, no intraday / F&O / margin / short.** Email
  is the only alert channel (Gmail SMTP), throttled, with a **PAPER-ONLY**
  reminder in every body.

---

For the staged path toward lower-latency (and eventually, far in the future,
gated live) execution — and why even fast action still requires the same hard
risk gates — see [`docs/future_realtime_execution.md`](future_realtime_execution.md).
