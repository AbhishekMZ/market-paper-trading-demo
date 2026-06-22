# Future Real-Trading Transition

> **v1 is paper-trading only.** This document describes the *later* path to real
> trading. None of it is enabled now. Real Angel One execution is intentionally
> inert in v1 (see `src/broker/angel_one_stub.py`).

The whole point of the broker-adapter design is that the strategy, risk, and
execution engines never change when we move to real trading — only the
**adapter** behind the `BrokerAdapter` interface is swapped, and only after
strict validation.

---

## Step 1 — Keep the engine, swap only the adapter

- Keep the **same signal/strategy engine** (`src/strategy/`).
- Keep the **same risk engine** (`src/risk_engine.py`).
- Keep the **same execution engine** (`src/execution_engine.py`).
- Replace `PaperBrokerAdapter` with `AngelOneBrokerAdapter` **only after**
  one month (ideally more) of paper validation looks good.

The rest of the system talks to `BrokerAdapter` only, so this is a localized change.

### Strategy eligibility gate (new in the hybrid design)
A strategy may **not** inform real trading unless its hypothesis in
`config/research_hypotheses.yml` has `validation_status` of either
`accepted_for_manual_review` or `accepted_for_limited_live_later`
(`ResearchRegistry.is_real_trading_eligible`). Popular ≠ valid. Every strategy
must earn its weight with paper-trading evidence first.

---

## Step 2 — Wire up the real adapter (still disabled by default)

- Add Angel One credentials via **GitHub/host secrets**, never committed:
  `ANGEL_ONE_CLIENT_ID`, `ANGEL_ONE_PASSWORD`, `ANGEL_ONE_TOTP_SECRET`,
  `ANGEL_ONE_API_KEY`, (+ feed/jwt tokens obtained at login).
- Implement in `AngelOneBrokerAdapter` (currently a disabled stub):
  - SmartAPI authentication (TOTP-based login) — see the `TODO`s in the stub.
  - Real holdings sync, order-book sync, trade-book sync.
  - Live LTP source.
- Add a manual-approval UI (the dashboard already shows execution mode; add
  Approve/Reject actions that write to `data/state/approvals.json`).
- Keep `live_trading_enabled: false` by default.

---

## Step 3 — Manual-approval real trading (Phase 2/3)

- Enable **manual-approval mode only**. The user must approve **every** real order.
- Equity **delivery only**. **Limit orders only**.
- **₹2,000** max per trade. Monthly cap enforced. (`risk_engine.py` already does this.)
- No automatic real orders.

---

## Step 4 — Carefully controlled automation (Phase 4)

Only after **months** of paper + manual validation, and only behind explicit flags:

- Require an **emergency kill switch** (`execution_state.kill_switch`).
- Require a **daily loss cap** and a **max order count**.
- Require **broker health checks** before each session.
- Require **data-quality checks** (already present — weak data ⇒ no trade).
- Require **audit logging** for every order attempt (already present).

The system must remain *off* unless every one of these is explicitly enabled.

---

## Step 5 — Deployment & regulatory reality

- Real Angel One/SmartAPI order placement may require a **static IP / IP
  whitelisting** or other broker/API conditions. If so, **GitHub Actions is not
  suitable for real execution** (its runners have dynamic IPs). A separate,
  controlled deployment (e.g. a small VPS you trust) would be needed for the
  *execution* path. GitHub Actions can still run analysis/reporting.
- Add order tags / client-order-ids for traceability where the broker supports them.
- Understand the regulatory context for retail algo trading in India (broker
  approval of strategies/algos, exchange rules, audit trails). Treat this as a
  prerequisite, not an afterthought.

---

## Safety checklist before enabling ANY real order

- [ ] ≥ 1 month of paper trading reviewed; results understood (not just P&L).
- [ ] Out-of-sample validation done (not threshold-tuned to the demo month).
- [ ] Strategy hypotheses marked `accepted_for_manual_review`.
- [ ] Manual-approval mode implemented and tested on paper.
- [ ] Kill switch, daily loss cap, max order count configured.
- [ ] Credentials stored only as secrets; nothing committed.
- [ ] Broker health check + data-quality check gate each session.
- [ ] Deployment IP/whitelisting requirements understood.
- [ ] `broker.yml` safety confirmations all set true **intentionally**.

Until every box is checked, the only safe and correct mode is **paper**.
