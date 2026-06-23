# Future Real-Time Execution

> ⚠️ **v1 is PAPER TRADING ONLY, and stops at Phase 1.** This document describes
> the *later*, still-gated, paper-first path toward lower-latency observation and
> — far in the future, only after heavy validation — limited live automation.
> **None of Phases 2–4 are enabled now.** Speed is never a reason to weaken a
> safety gate. See also [`docs/future_real_trading_transition.md`](future_real_trading_transition.md)
> for the broker-adapter swap details.

The Observation & Escalation Engine (`src/observation/`, see
[`docs/observation_escalation_engine.md`](observation_escalation_engine.md))
exists to react *between* the fixed deep-analysis checkpoints. Today it runs on
GitHub Actions, takes only **paper** action, and is deliberately low-noise. The
phases below describe how its *latency* could improve over time — **every step
still paper-first or manual-approval**, and every order still passing the same
hard gates.

---

## Phase 1 — GitHub Actions observation (where v1 is)

- Observation runs on **GitHub Actions**, manual `workflow_dispatch` by default
  (`observe.yml`), with example schedules **commented out**. Target cadence when
  scheduled: every **30–60 minutes** between checkpoints.
- **Paper-only.** Swift action means a swift **paper** buy (via
  `ExecutionEngine.process_buy`) or a manual-review **email** alert. Sell is
  review-only.
- **Limitations are accepted on purpose:** GitHub Actions is **not** a precision
  real-time engine — cron jitter, ephemeral runners, no intraday guarantees. v1
  keeps the watchlist small, the caps tight, and the schedule manual to stay
  ₹0-cost and trustworthy.

**This is where v1 deliberately stops.**

---

## Phase 2 — Local always-on observer (future)

- A **long-running process / cron on a laptop or home machine** runs
  `--observe-only` on a tighter interval than Actions allows.
- **Lower latency** than GitHub Actions (no runner spin-up, no cron jitter), so
  triggers are seen sooner.
- **Still paper-only, or manual-approval at most.** No real orders. The same
  `ExecutionEngine`, Risk, News, and DataQuality gates apply unchanged.
- Trade-offs: the machine must stay on, and state lives locally — but this is
  cheap, private, and a safe way to validate that lower latency actually adds
  value before any infrastructure spend.

---

## Phase 3 — VPS / static-IP observer with broker market data (future)

- A small **VPS / static-IP host** runs the observer, optionally fed by a real
  **broker market feed** (e.g. an Angel One market feed) for fresher, more
  reliable quotes than the unofficial `yfinance` source.
- **Manual approval is required for any REAL order** — no automatic live
  execution. Real order placement may require **IP whitelisting / a static IP**,
  which is one reason GitHub Actions (dynamic IPs) is unsuitable for the
  *execution* path.
- New operational requirements appear here and must be treated as prerequisites,
  not afterthoughts:
  - a **static IP** / whitelisting arrangement with the broker,
  - proper **secrets management** (credentials only as host secrets, never
    committed),
  - **monitoring / alerting / health checks** on the always-on process.
- Even with a live market feed, the system still places **paper** trades unless a
  human explicitly approves a real one through the manual-approval flow.

---

## Phase 4 — Limited live automation (far future, heavily gated)

Only after **all** of the following — and only behind explicit flags:

- **Regulatory / broker requirements** satisfied (SEBI context for retail algo
  trading in India; broker/API terms; exchange rules; audit trails).
- **Risk controls** in place and tested: emergency **kill switch**, **daily loss
  cap**, **max order count**, broker **health checks**, and the existing
  data-quality + audit-logging gates.
- **MONTHS of validated paper performance** plus **decision-quality evidence**
  (forward returns, benchmark-vs-NIFTY, strategy attribution) showing the edge is
  real — not threshold-tuned to one demo month.

Even then, automation is **limited**: equity **delivery only**, **LIMIT orders
only**, **₹2,000** max per trade, monthly cap enforced, and the system stays
**off** unless every control is explicitly, intentionally enabled. The full
checklist lives in
[`docs/future_real_trading_transition.md`](future_real_trading_transition.md).

---

## Why swift action still requires hard risk gates

Lower latency changes **when** the system can act — it must **never** change
**whether** an action is safe. At *every* phase, *every* order (paper or, much
later, real) passes the **same** gates:

- **Risk** — position sizing, per-trade cap (₹2,000), daily/monthly buy limits.
- **News** — adverse news can block/downgrade a buy; **news can never create or
  upgrade one.**
- **Data quality** — anomalous / stale / insufficient data ⇒ **no action.**
- **ExecutionEngine** — the single chokepoint
  (`ExecutionEngine.process_buy`/`validate_safety`): LIMIT + DELIVERY +
  paper-only in v1; no market orders, no intraday/F&O/margin/short.

The whole point of the observer is that it **reuses the deep pipeline's engines**
rather than running a faster, weaker, parallel set of rules. A swift paper buy
and a deep-checkpoint paper buy go through the **identical** code path. As speed
increases across phases, the gates do **not** get relaxed to keep up — if a gate
would slow an order, the order waits or is dropped. **Speed must never bypass
safety.**

A faster observer that skipped a gate would be strictly *worse* than the slow,
safe one: it would just lose money faster. So the rule is absolute — there is no
"fast path" that avoids Risk / News / DataQuality / ExecutionEngine, in any phase.

---

> **v1 deliberately stops at Phase 1.** Lower-latency and live phases are
> described here so the design intent is clear — but they are **not** built,
> **not** enabled, and gated behind validation, regulation, and explicit human
> control. Until all of that is in place, the only safe and correct mode is
> **paper**.
