# Project Roadmap — Indian Equity Paper-Trading Demo

**Living document. Planning only — listing something here is not a commitment to
build it, and nothing here is implemented until it has its own spec → plan →
approved execution.** Last updated: 2026-06-27.

This is the single place future sessions should look to pick up cleanly: what's
queued, in what order, what each item depends on, and where its spec/plan lives.

---

## Standing constraints (binding — apply to every item below)

- **Paper-trading only.** No real broker execution, no Angel One credentials, no
  live orders. The CI "safety gate" fails the run if `active_adapter != "paper"`
  or any of `live_trading_enabled` / `allow_real_orders` / `angel_one_enabled`
  is true.
- **₹0 cost.** GitHub Actions (ephemeral, ~3×/weekday) + GitHub Pages (static).
  yfinance for data (no API key). No paid services.
- **Email-only alerts** to `sahabhi115@gmail.com`. No WhatsApp/Telegram.
- **Caution-first.** Overlays may only *add* caution (downgrade/block a buy);
  they never create or upgrade a buy and never mutate the 0–100 score.
- **No self-optimization / no ML in v1.** Deterministic, explainable, auditable.
  See `docs/strategy_validation_principles.md`.
- **PR workflow.** Direct push to `main` is blocked. Merging is the user's call.

Any item that would change these is, by definition, a larger decision and must
say so explicitly.

---

## Status legend

| Mark | Meaning |
|---|---|
| ✅ done | Merged to `main`. |
| 📦 ready | Spec + plan written and committed; not yet implemented. |
| 🧭 needs spec | Agreed in principle; needs its own brainstorm → spec → plan. |
| 💤 parked | Deliberately deferred; revisit only when a trigger condition is met. |

---

## Sequencing at a glance

```
NOW  ──► A. Historical-context overlay      (📦 ready to implement)
NEXT ──► C. Sentiment line on DecisionTrace (small FE; unblocked)
         B. Backend + DB migration          (🧭 needs its own spec)
LATER─► E. Honest price-only validation      (🧭, heavily caveated)
         F. Dashboard polish                 (opportunistic)
```

Recommended path: **A → C → B**, with **E** and **F** slotted in opportunistically.
A and C are independent of each other; B is the big one and should follow A.

---

## Backlog

### A. Historical-context caution overlay  📦 ready
Trailing-only 2-year price features (vol percentile, 2y range position, DMA
extension, drawdown, beta vs NIFTY, liquidity, trend persistence) fed into the
live pipeline as a **caution-only** overlay mirroring `NewsRiskEngine`.

- **Spec:** `docs/superpowers/specs/2026-06-27-historical-context-overlay-design.md`
- **Plan:** `docs/superpowers/plans/2026-06-27-historical-context-overlay.md` (8 TDD tasks, complete code)
- **Branch:** `feature/historical-context-overlay` (local only — not pushed)
- **Storage:** committed JSON (`data/state/historical_context.json` + `public/data`).
- **Depends on:** nothing. **Blocks:** D (its Task 8 is the dashboard surface).
- **Next action:** implement via subagent-driven-development when the user says go.

### B. Backend + database migration  🧭 needs spec
Move off static Pages + committed JSON to a live backend (Vercel/Render) + a
database (Mongo **or** Postgres). A DB only makes sense *with* an always-on
backend, because a static Pages site cannot query a DB — so this bundles
hosting + API + DB into one effort.

- **Memory:** `backend-db-migration-plan`
- **Depends on:** A merged first (per the user's sequencing decision).
- **Notes:** all disk I/O funnels through `src/storage.py`, so the JSON→DB swap
  is localized. Mongo-vs-Postgres deferred to this spec. This is the trigger that
  un-parks **Vercel/Render** (see Parked).
- **Next action:** brainstorm → spec → plan as its own cycle after A ships.

### C. Sentiment line on the `Why` / `DecisionTrace` view  🧭 small
Surface `sentiment · confidence · sources-agree` on the decision-trace UI. This
was "Task 10" deferred during the sentiment work; **now unblocked** because both
`DecisionTrace.jsx` (PR #9) and the sentiment fields (PR #10) are on `main`.

- **Depends on:** nothing (its blockers are merged). Small, self-contained FE PR.
- **Next action:** confirm the exact field/line, implement, open a small PR.

### D. `Why`-view historical-context line  📦 (bundled in A)
One line rendering `hist_*` fields (vol pctile · range · β · context flags),
guarded to show nothing when context is unavailable.

- **Spec/plan:** Task 8 of plan A (marked optional/last).
- **Depends on:** A implemented + on `main`.

### E. Honest price-only validation (walk-forward)  🧭 caveated
The project deliberately ships `replay_full_history` and the walk-forward
validator as `NotImplementedError` placeholders. A *price-only*, explicitly
indicative walk-forward (no historical news, clearly labeled "not a profitability
claim") could be built now that yfinance provides 2y adjusted bars.

- **Read first:** `docs/strategy_validation_principles.md`, `src/backtesting/README.md`.
- **Risk:** survivorship/look-ahead/overfitting — must be framed as descriptive,
  never as a profitability promise. Needs its own careful spec.
- **Depends on:** nothing technically; conceptually benefits from A's feature code.

### F. Dashboard polish  💤 opportunistic
Small UX items: a manual "Refresh" button in the header; optionally more weekday
cron slots in `analyze.yml` for finer intraday snapshots (still ₹0 within Actions
limits; does nothing on weekends). The auto-refresh poll (every 60s + on focus)
already shipped in PR #11.

---

## Parked (revisit only on a trigger)

- **Vercel/Render live deployment.** 💤 Parked. Current Actions → Pages already
  serves the read-only dashboard at ₹0. **Trigger to revisit:** starting item B
  (a live sentiment/context API only matters with a backend).
- **WhatsApp / Telegram / SMS alerts.** 💤 Out of scope by standing constraint
  (email-only).
- **Real-broker / Angel One execution.** 💤 Out of scope in v1 by the safety gate.
- **ML / self-tuning strategies.** 💤 Out of scope in v1 by design.

---

## Housekeeping notes

- This repo's local folder is `finance_mmg`; its GitHub remote is
  `AbhishekMZ/market-paper-trading-demo` (public). The name mismatch is cosmetic
  and intentional to keep — not a misconfiguration.
- The initial commit is mislabeled *"RL-Enhanced Music Learning Application"* — a
  harmless leftover; can be clarified in the README if it causes confusion.

## How to maintain this doc

When an item ships, flip it to ✅ and move it out of the sequencing diagram. When
a new idea appears, add it under Backlog with a status mark and (if agreed) a
"needs spec" note — don't start building from this doc; each item earns its own
spec → plan first.
