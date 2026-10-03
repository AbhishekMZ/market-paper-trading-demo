# Project Roadmap — Indian Equity Paper-Trading Demo

**Living document. Planning only — listing something here is not a commitment to
build it, and nothing here is implemented until it has its own spec → plan →
approved execution.** Last updated: 2026-10-03.

This is the single place future sessions should look to pick up cleanly: what's
queued, in what order, what each item depends on, and where its spec/plan lives.

---

## Standing constraints (binding — apply to every item below)

- **Paper-trading only.** No real broker execution, no Angel One credentials, no
  live orders. The CI "safety gate" fails the run if `active_adapter != "paper"`
  or any of `live_trading_enabled` / `allow_real_orders` / `angel_one_enabled`
  is true.
- **₹0 cost.** GitHub Actions (ephemeral checkpoints + low-noise observe) +
  GitHub Pages (static). yfinance for data (no API key). No paid services.
- **Email-only alerts** to `sahabhi115@gmail.com`. No WhatsApp/Telegram.
- **Caution-first.** Overlays may only *add* caution (downgrade/block a buy);
  they never create or upgrade a buy and never mutate the 0–100 score.
- **No silent self-optimization.** Learning may **propose** paper-config changes;
  humans (or an explicit future gated path) apply them. Readiness never enables
  live trading. See `docs/strategy_validation_principles.md`.
- **PR workflow.** Direct push to `main` is blocked. Merging is the user's call.

Any item that would change these is, by definition, a larger decision and must
say so explicitly.

---

## Status legend

| Mark | Meaning |
|---|---|
| ✅ done | Merged to `main`. |
| 🚧 in progress | Spec/plan exists; implementation underway on working tree / PR. |
| 📦 ready | Spec + plan written and committed; not yet implemented. |
| 🧭 needs spec | Agreed in principle; needs its own brainstorm → spec → plan. |
| 💤 parked | Deliberately deferred; revisit only when a trigger condition is met. |

---

## Sequencing at a glance

```
NOW  ──► News robustness + trailing price windows (same JSON store)
         G. Learning proposals (suggest-only)
         A. Historical-context overlay      (caution-only; features reused by the score)
LATER─► C. Sentiment line on DecisionTrace (small FE)
         E. Honest price-only validation      (🚧 partial — PriceOnlyReplay shipped)
         F. Dashboard polish                 (opportunistic)
PARKED ► B. Backend + Postgres             (triggers below; not Phase 4)
         Phase 4 live automation            (evidence + controls, not storage)
```

---

## Backlog

### A. Historical-context caution overlay  📦 ready / 🚧 implementing
Trailing-only 2-year price features fed into the live pipeline as a
**caution-only** overlay mirroring `NewsRiskEngine`.

- **Spec:** `docs/superpowers/specs/2026-06-27-historical-context-overlay-design.md`
- **Plan:** `docs/superpowers/plans/2026-06-27-historical-context-overlay.md`
- **Depends on:** nothing. **Blocks:** D (dashboard hist line).

### B. Backend + Postgres  💤 parked
Move off static Pages + committed JSON only when a trigger below is true.
I/O already funnels through `src/storage.py`, so the swap stays local.
**Postgres** is the engine if this starts. A later live path reads the same
store for quotes, the decision-time news archive, signals, and orders. It does
not make a feature more accurate, and it is not a step toward Phase 4.

Triggers (any one):

- An always-on observer and the dashboard must read and write the same state.
- News and signal history must be queried by symbol and time, not shipped as
  committed JSON.
- The git-committed `data/` and `public/data/` copies become too large or too
  easy to corrupt.

### C. Sentiment line on the `Why` / `DecisionTrace` view  🚧
Surface `sentiment · confidence · sources-agree` on the decision-trace UI.

### D. `Why`-view historical-context line  📦 (bundled in A Task 8)
Depends on A implemented.

### E. Honest price-only validation  🚧 partial
`PriceOnlyReplay` + `mmg.py backfill` shipped (descriptive, price strategies
only). Full-pipeline `replay_full_history` / walk-forward remain placeholders.
See `src/backtesting/README.md`.

### F. Dashboard polish  💤 opportunistic
Refresh button / extra cron slots as needed. Auto-refresh poll already shipped.

### G. Learning proposals (suggest-only)  🚧
`mmg.py learn propose` + `config/learning.yml`. Measure → propose → human
`profile apply`. **No silent auto-mutate of default CI config. Never enables live.**

---

## Parked (revisit only on a trigger)

- **Phase 4 — limited live automation with a kill switch.** 💤 Not justified
  while paper evidence is thin (learning proposal: not enough matured episodes;
  see `docs/LIVE_READINESS.md`). Blocked on evidence, manual-approval history,
  and the controls in `docs/future_real_trading_transition.md`. A database does
  not clear that bar.
- **Vercel/Render live deployment.** 💤 Trigger: starting item B.
- **WhatsApp / Telegram / SMS alerts.** 💤 Email-only constraint.
- **Real-broker / Angel One execution.** 💤 Safety gate / v1.
- **Closed-loop ML auto-tuning of default config.** 💤 Remains parked; G is
  propose/human-gated only until principles are explicitly revised.

---

## Housekeeping notes

- Local folder `finance_mmg`; GitHub remote `AbhishekMZ/market-paper-trading-demo`.
- Evidence status (2026-07-16 artifacts): 1 paper trade, readiness
  `NOT_ENOUGH_DATA`; NEUTRAL gating + small historical universe starved buys.
  Pipeline hardening (CSV coverage reporting, `evidence` profile,
  `neutral_min_confidence`, NSE holidays, observe schedule) addresses this
  without enabling live trading.

## How to maintain this doc

When an item ships, flip it to ✅ and move it out of the sequencing diagram. When
a new idea appears, add it under Backlog with a status mark — don't start
building from this doc alone; each item earns its own spec → plan first.
