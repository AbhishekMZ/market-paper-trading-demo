# Simplified XAI Dashboard — Design

**Date:** 2026-06-26
**Status:** Approved (design)
**Scope:** Frontend only. No backend, config, or workflow changes.

## Problem

The dashboard has grown to **14 nav tabs / 36 components / 22 data files**. This app is
primarily a backend (a scheduled, unattended paper-trading engine); the frontend is a
read-only window onto it. Most tabs are niche operational panels that the user never
needs, and the one thing that matters — *why did the engine make the calls it made?* — is
buried.

## Key insight

The backend **already emits a complete, human-readable decision trace per stock** inside
`public/data/latest_report.json`. Each signal carries:

- `score` (0–100), `label` (BUY_SMALL_PAPER / WATCH / NO_ACTION / DO_NOT_BUY /
  HIGH_RISK_IGNORE), `confidence`, `risk_level`, `last_price`, `led_to_paper_trade`
- `score_breakdown` — per-strategy numeric contribution
- `strategy_results[]` — for each of 7 strategies: `signal` (POSITIVE/NEGATIVE/NEUTRAL),
  `score_contribution`, `contributes_to_score`, and a **plain-English `reason`**
  (e.g. *"Trend +8.07% over 24 points, smoothness 61%."*)
- `reason` — signal-level summary incl. disagreement detection
  (*"Top: trend_following=88, portfolio_fit=80 … Disagreement: [...] positive vs [...] negative"*)
- News/data/budget gates: `news_risk_level`, `news_blocks_buy`, `news_reasons`,
  `data_quality_verdict`, `price_consistency_check`

So the "XAI" is a **presentation** problem, not a modelling one. The frontend renders the
engine's *own* reasons — it never re-derives decision logic, so the explanation cannot
drift from the actual decision. This keeps the work FE-only: **no CI safety-gate risk, no
config change, ₹0 deploy pipeline untouched.**

## Design

### Navigation: 14 tabs → 3 views

**1 · Today** (default landing)
- Existing paper banner + status strip (PAPER ONLY · Live OFF · Angel One DISABLED · last updated).
- Snapshot row: total value, total P&L, open positions, **buys X/100**, budget used / remaining.
- One-line headline derived from the report (e.g. *"Scanned 10 names, 0 buys — top pick SBIN (69) fell short of the buy bar."*).
- **Today's calls** table: symbol · name · score · label · one-line reason · last price.
  Clicking a row navigates to **Why**, focused on that stock.

**2 · Why** (XAI — narrative + per-stock traces)
- **Narrative** (top): a plain-English paragraph assembled from the report — market regime,
  count scanned, count bought, the top pick and why it did/didn't fire, and budget posture.
- **Per-stock decision-trace cards** (below), one per scanned name:
  - Header: symbol · name · label pill · score
  - Verdict line: e.g. `69 → WATCH (buy bar not met)`
  - Strategy votes: all 7 strategies, each shown as ✓ (used, positive) / ✗ (used, negative) /
    · (not counted), with its numeric weight and the engine's `reason` text. Sorted
    used-first, then by contribution.
  - Score bar visualizing the final score.
  - Gates row: News (OK / blocks-buy + worst headline), Data quality, Budget, plus the
    disagreement note when present.
  - The card matching `focusSymbol` (from a Today click) starts expanded; others collapsed.

**3 · Track Record** (is it actually working?)
- Consolidates the useful parts of the current 5 evaluation tabs into one screen:
  - **Maturity / evidence** — reuse `EvidenceSummary` (today: COLLECTING_EVIDENCE, 41.7%).
  - **Portfolio vs NIFTY** — reuse `BenchmarkComparison` (AHEAD/BEHIND).
  - **Cost-adjusted realized P&L + win rate** — from `latest_report.json.cost_adjusted_pnl`.
  - **Acted-vs-shadow edge** — does a high score actually precede better forward returns?
    (from `decision_quality.json`).

### Build / reuse / archive

- **New files:**
  - `frontend/src/lib/narrative.js` — pure functions: build the narrative string and
    classify/sort strategy votes from a report object. No React, trivially checkable.
  - `frontend/src/components/DecisionTrace.jsx` — the per-stock card.
  - `frontend/src/views/Today.jsx`, `frontend/src/views/Why.jsx`,
    `frontend/src/views/TrackRecord.jsx` — thin view wrappers composing existing pieces.
    (Today's `Dashboard.jsx` becomes the basis for `Today.jsx`.)
- **Reused as-is:** `EvidenceSummary`, `BenchmarkComparison`, `MarketRegimeCard`,
  `ui.jsx` primitives, `lib/format.js`, the dark theme in `styles.css` (small additions for
  vote rows + score bar).
- **Archived:** the remaining ~30 components stay in the repo and keep receiving their JSON;
  they are simply removed from `App.jsx`'s nav. Fully reversible — nothing deleted.

### Cross-view linking

`App.jsx` owns `{ activeView, focusSymbol }`. Clicking a Today row sets
`activeView='why'` + `focusSymbol=<symbol>`; the Why view expands and scrolls to that
card. Small contained state, no router dependency.

### Data sources (all already committed in `public/data/`)

- Today + Why: `latest_report.json` (signals, score_breakdown, strategy_results, reasons,
  portfolio, market_regime, no_trade_reasons).
- Track Record: `latest_report.json.cost_adjusted_pnl` + `decision_quality.json`.

## Non-goals

- No backend / Python / config / workflow changes.
- No change to safety posture: paper-only, live trading DISABLED, email-only alerts — all
  unchanged and still surfaced in the UI.
- Not deleting the archived components (reversible by design).
- No new data files; narrative is assembled client-side from existing report fields.

## Verification

- `npm run build` must compile cleanly.
- Local `vite preview` smoke test of all 3 views, incl. the Today→Why click-through.
- `narrative.js` kept as pure functions for trivial reasoning/optional unit checks.
- Revert any committed demo-data files that the build/test dirties before committing
  (source-only diff), per existing repo discipline.

## Risks

- **Stale `latest_report.json` on first load** — mitigated: cards render from whatever the
  report contains and degrade gracefully (empty/"no data" states via existing `DataGate`).
- **Archived components drifting** — acceptable; they remain buildable and reachable via git;
  if any becomes truly dead we can delete later in a separate pass.
