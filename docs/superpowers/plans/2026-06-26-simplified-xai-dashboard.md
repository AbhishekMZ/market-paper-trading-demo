# Simplified XAI Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the 14-tab dashboard to 3 focused views (Today / Why / Track Record) and surface the engine's own per-stock decision trace as an explainable-AI "Why" view.

**Architecture:** Frontend-only. A new pure-JS `narrative.js` turns `latest_report.json` into plain-English summaries; a new `DecisionTrace` card composes the existing `StrategyBreakdown` with a verdict + gates row; three thin view wrappers replace the old tab soup; `App.jsx` is rewired to 3 tabs with a `focusSymbol` for Today→Why click-through. The ~30 unused components stay in the repo (archived, dropped from nav). No backend, config, or workflow changes.

**Tech Stack:** React 18 + Vite (static), plain ES modules, Node for a framework-free unit test.

---

## File Structure

| File | Responsibility | Action |
| --- | --- | --- |
| `frontend/src/lib/narrative.js` | Pure functions: roll a report into counts + plain-English headline/paragraph; order strategy votes. No React. | Create |
| `frontend/scripts/test_narrative.mjs` | Framework-free Node unit checks for `narrative.js`. | Create |
| `frontend/src/components/DecisionTrace.jsx` | Per-stock "why" card: verdict line + gates row + collapsible `StrategyBreakdown`. | Create |
| `frontend/src/views/Today.jsx` | Snapshot tiles + run headline + clickable calls table (row → Why). | Create |
| `frontend/src/views/Why.jsx` | Narrative paragraph + list of `DecisionTrace` cards; auto-expands/scrolls `focusSymbol`. | Create |
| `frontend/src/views/TrackRecord.jsx` | Maturity (`EvidenceSummary`) + cost-adjusted realised P&L + `BenchmarkComparison`. | Create |
| `frontend/src/App.jsx` | 3-tab nav + `focusSymbol` state + cross-view nav. | Modify |
| `frontend/src/styles.css` | Small additions for the decision-trace verdict/gates/toggle. | Modify |

Reused unchanged: `StrategyBreakdown.jsx`, `EvidenceSummary.jsx`, `BenchmarkComparison.jsx`, `ui.jsx`, `lib/format.js`, `hooks/useData.js`. Archived (left in repo, dropped from nav): all other `components/*.jsx`.

**Branch:** `feature/simplified-xai-dashboard` (already checked out; spec already committed there).

**Working directory note:** run all `npm`/`node` commands from `frontend/`. If a shell `cd`/`Set-Location` persists, reset to `C:\Users\Mishael Abhishek\Projects\finance_mmg` before any `git`/search command.

---

### Task 1: Narrative module (pure logic, TDD)

**Files:**
- Create: `frontend/scripts/test_narrative.mjs`
- Create: `frontend/src/lib/narrative.js`

- [ ] **Step 1: Write the failing test**

Create `frontend/scripts/test_narrative.mjs`:

```js
// Plain-Node unit checks for the narrative helpers (no test framework needed).
// Run from the frontend/ directory:  node scripts/test_narrative.mjs
import assert from 'node:assert/strict';
import {
  summarizeRun,
  runHeadline,
  runNarrative,
  orderStrategyVotes,
} from '../src/lib/narrative.js';

const report = {
  market_regime: { regime: 'NEUTRAL' },
  checkpoint: 'close',
  portfolio: {
    buys_this_month: 1,
    max_buys_per_month: 100,
    capital_remaining: 8475,
    monthly_capital: 10000,
  },
  signals: [
    { symbol: 'SBIN.NS', name: 'State Bank of India', score: 69.2, label: 'WATCH', led_to_paper_trade: false },
    { symbol: 'ITC.NS', name: 'ITC', score: 41.9, label: 'DO_NOT_BUY', led_to_paper_trade: false },
    { symbol: 'TCS.NS', name: 'TCS', score: 32.1, label: 'HIGH_RISK_IGNORE', led_to_paper_trade: false },
  ],
};

// summarizeRun ------------------------------------------------------------
const s = summarizeRun(report);
assert.equal(s.scanned, 3, 'scanned count');
assert.equal(s.bought, 0, 'no buys');
assert.equal(s.watch, 1, 'one watch');
assert.equal(s.avoid, 2, 'two avoid');
assert.equal(s.regime, 'NEUTRAL', 'regime');
assert.equal(s.topPick.symbol, 'SBIN.NS', 'top pick is highest score');
assert.equal(s.topPick.acted, false, 'top pick not acted');
assert.equal(s.budget.buysCap, 100, 'buy cap');

// runHeadline -------------------------------------------------------------
const h = runHeadline(report);
assert.match(h, /Scanned 3 names/, 'headline scanned');
assert.match(h, /0 buys/, 'headline buys');
assert.match(h, /SBIN\.NS/, 'headline top pick');
assert.match(h, /fell short/, 'headline shortfall');

// runNarrative ------------------------------------------------------------
const n = runNarrative(report);
assert.ok(Array.isArray(n) && n.length >= 3, 'narrative has sentences');
assert.match(n.join(' '), /neutral market/, 'narrative regime');
assert.match(n.join(' '), /1\/100 monthly buys used/, 'narrative budget');

// orderStrategyVotes: counted-first, then contribution desc ---------------
const ordered = orderStrategyVotes([
  { strategy_name: 'a', contributes_to_score: false, score_contribution: 90 },
  { strategy_name: 'b', contributes_to_score: true, score_contribution: 50 },
  { strategy_name: 'c', contributes_to_score: true, score_contribution: 80 },
]);
assert.deepEqual(ordered.map((r) => r.strategy_name), ['c', 'b', 'a'], 'vote ordering');

// empty-input safety ------------------------------------------------------
assert.equal(summarizeRun({}).scanned, 0, 'empty report safe');
assert.ok(runHeadline({}).length > 0, 'empty headline safe');
assert.ok(Array.isArray(runNarrative({})), 'empty narrative safe');

console.log('OK: narrative helpers pass');
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `frontend/`): `node scripts/test_narrative.mjs`
Expected: FAIL — `Cannot find module '../src/lib/narrative.js'` (file not created yet).

- [ ] **Step 3: Write the implementation**

Create `frontend/src/lib/narrative.js`:

```js
// Pure, framework-free helpers that turn a latest_report.json object into the
// plain-English "what the engine did" narrative shown on the Today + Why views.
// No React and no imports from .jsx — safe to unit-test under plain Node.

// Labels that represent an actual paper buy vs. an explicit "avoid".
const BUY_LABELS = new Set(['BUY_SMALL_PAPER']);
const AVOID_LABELS = new Set(['DO_NOT_BUY', 'HIGH_RISK_IGNORE']);

function num(v, fallback = 0) {
  const n = Number(v);
  return Number.isNaN(n) ? fallback : n;
}

function humanRegime(regime) {
  return String(regime || 'unknown').toLowerCase().replace(/_/g, ' ');
}

function labelText(label) {
  return String(label || '—').replace(/_/g, ' ').toLowerCase();
}

function inr(n) {
  return Number(num(n)).toLocaleString('en-IN');
}

/**
 * Roll a report up into the counts + highlights the narrative needs.
 * Pure: depends only on its argument.
 */
export function summarizeRun(report) {
  const r = report || {};
  const signals = Array.isArray(r.signals) ? r.signals : [];
  const regime = (r.market_regime && r.market_regime.regime) || 'UNKNOWN';

  let bought = 0;
  let watch = 0;
  let avoid = 0;
  let top = null;
  for (const sig of signals) {
    if (sig.led_to_paper_trade || BUY_LABELS.has(sig.label)) bought += 1;
    else if (sig.label === 'WATCH') watch += 1;
    else if (AVOID_LABELS.has(sig.label)) avoid += 1;
    if (top === null || num(sig.score) > num(top.score)) top = sig;
  }

  const p = r.portfolio || {};
  return {
    scanned: signals.length,
    bought,
    watch,
    avoid,
    regime,
    topPick: top
      ? {
          symbol: top.symbol,
          name: top.name,
          score: num(top.score),
          label: top.label,
          acted: Boolean(top.led_to_paper_trade) || BUY_LABELS.has(top.label),
        }
      : null,
    budget: {
      buysUsed: num(p.buys_this_month),
      buysCap: num(p.max_buys_per_month),
      capitalRemaining: num(p.capital_remaining),
      monthlyCapital: num(p.monthly_capital),
    },
  };
}

/** A single tight sentence for the Today header. */
export function runHeadline(report) {
  const s = summarizeRun(report);
  if (s.scanned === 0) return 'No stocks were scored in this run.';
  const buys = `${s.bought} ${s.bought === 1 ? 'buy' : 'buys'}`;
  if (!s.topPick) return `Scanned ${s.scanned} names, ${buys}.`;
  const tp = s.topPick;
  const tail = tp.acted
    ? `top pick ${tp.symbol} (${tp.score.toFixed(0)}) cleared the buy bar.`
    : `top pick ${tp.symbol} (${tp.score.toFixed(0)}) fell short of the buy bar.`;
  return `Scanned ${s.scanned} names, ${buys} — ${tail}`;
}

/** A short paragraph (array of sentences) for the Why view. */
export function runNarrative(report) {
  const s = summarizeRun(report);
  const out = [];
  if (s.scanned === 0) {
    out.push('This run scored no stocks, so there is nothing to explain yet.');
    return out;
  }
  out.push(
    `In a ${humanRegime(s.regime)} market, the engine scored ${s.scanned} ` +
      `${s.scanned === 1 ? 'name' : 'names'} and made ${s.bought} paper ` +
      `${s.bought === 1 ? 'buy' : 'buys'}.`,
  );
  if (s.topPick) {
    const tp = s.topPick;
    out.push(
      tp.acted
        ? `The strongest candidate, ${tp.symbol} (${tp.score.toFixed(0)}/100), cleared the bar and was bought on paper.`
        : `The strongest candidate, ${tp.symbol} (${tp.score.toFixed(0)}/100), still fell short of the buy bar and was left as ${labelText(tp.label)}.`,
    );
  }
  out.push(
    `${s.watch} ${s.watch === 1 ? 'name is' : 'names are'} on watch and ` +
      `${s.avoid} ${s.avoid === 1 ? 'was' : 'were'} flagged to avoid.`,
  );
  if (s.budget.buysCap > 0) {
    out.push(
      `Budget: ${s.budget.buysUsed}/${s.budget.buysCap} monthly buys used, ` +
        `₹${inr(s.budget.capitalRemaining)} of ₹${inr(s.budget.monthlyCapital)} still available.`,
    );
  }
  return out;
}

/**
 * Order a signal's strategy_results for display: strategies that actually
 * counted toward the score first, then by contribution (desc). Pure; returns a
 * new array and never mutates the input.
 */
export function orderStrategyVotes(results) {
  const list = Array.isArray(results) ? results.slice() : [];
  return list.sort((a, b) => {
    const au = a.contributes_to_score ? 1 : 0;
    const bu = b.contributes_to_score ? 1 : 0;
    if (au !== bu) return bu - au;
    return num(b.score_contribution) - num(a.score_contribution);
  });
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run (from `frontend/`): `node scripts/test_narrative.mjs`
Expected: prints `OK: narrative helpers pass`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/narrative.js frontend/scripts/test_narrative.mjs
git commit -m "feat(fe): narrative helpers for run summary + vote ordering"
```

---

### Task 2: DecisionTrace card + styles

**Files:**
- Create: `frontend/src/components/DecisionTrace.jsx`
- Modify: `frontend/src/styles.css` (append decision-trace styles)

- [ ] **Step 1: Add the styles**

Append to the end of `frontend/src/styles.css`:

```css
/* ---------- Decision trace (Why view) ---------- */
.trace-verdict {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}
.gate-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  align-items: center;
}
.gate {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.gate-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-dim);
  font-weight: 700;
}
.trace-toggle {
  appearance: none;
  align-self: flex-start;
  border: 1px solid var(--border);
  background: var(--surface-2);
  color: var(--text-muted);
  font: inherit;
  font-size: 12.5px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.trace-toggle:hover {
  color: var(--text);
  border-color: var(--accent);
}
```

- [ ] **Step 2: Create the component**

Create `frontend/src/components/DecisionTrace.jsx`:

```jsx
// Per-stock "why" card for the Why view. Renders the engine's own verdict, the
// news/data/budget gates, and (collapsible) the full per-strategy vote breakdown.
import { useState } from 'react';
import { Card, LabelPill } from './ui.jsx';
import { formatScore, formatINR } from '../lib/format.js';
import { orderStrategyVotes } from '../lib/narrative.js';
import StrategyBreakdown from './StrategyBreakdown.jsx';

// One-line plain-English verdict derived from the signal's label.
function verdict(s) {
  if (s.led_to_paper_trade || s.label === 'BUY_SMALL_PAPER')
    return `${formatScore(s.score)} → bought on paper`;
  if (s.label === 'WATCH') return `${formatScore(s.score)} → WATCH (buy bar not met)`;
  if (s.label === 'NO_ACTION') return `${formatScore(s.score)} → no action`;
  if (s.label === 'DO_NOT_BUY' || s.label === 'HIGH_RISK_IGNORE')
    return `${formatScore(s.score)} → avoided`;
  return `${formatScore(s.score)} / 100`;
}

function Gate({ label, value, tone = 'neutral' }) {
  return (
    <span className="gate">
      <span className="gate-label">{label}</span>
      <span className={`pill ${tone}`}>{value}</span>
    </span>
  );
}

export default function DecisionTrace({ signal: s, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const ordered = orderStrategyVotes(s.strategy_results || []);
  const newsBlocks = s.news_blocks_buy;
  const dataOk = (s.data_quality_verdict || 'OK') === 'OK';

  return (
    <Card
      title={`${s.symbol}${s.name ? ' · ' + s.name : ''}`}
      headRight={<LabelPill label={s.label} />}
    >
      <div className="card-pad stack" style={{ gap: 12 }}>
        <div className="trace-verdict">{verdict(s)}</div>

        <div className="gate-row">
          <Gate
            label="News"
            value={newsBlocks ? 'BLOCKS BUY' : s.news_risk_level || 'OK'}
            tone={newsBlocks ? 'danger' : 'ok'}
          />
          <Gate label="Data" value={s.data_quality_verdict || 'OK'} tone={dataOk ? 'ok' : 'warn'} />
          <Gate
            label="Est. cost"
            value={s.estimated_cost != null ? formatINR(s.estimated_cost) : '—'}
            tone="neutral"
          />
          <Gate
            label="Paper trade"
            value={s.led_to_paper_trade ? 'YES' : 'NO'}
            tone={s.led_to_paper_trade ? 'buy' : 'neutral'}
          />
        </div>

        {s.news_top_headline ? (
          <p className="muted small" style={{ margin: 0 }}>
            Top headline: {s.news_top_headline}
          </p>
        ) : null}

        <button className="trace-toggle" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
          {open ? 'Hide' : 'Show'} strategy votes ({ordered.length})
        </button>

        {open ? (
          <StrategyBreakdown results={ordered} conflicts={s.conflict_warnings || []} />
        ) : null}
      </div>
    </Card>
  );
}
```

- [ ] **Step 3: Verify it compiles**

Run (from `frontend/`): `npm run build`
Expected: build succeeds (`✓ built in …`). Vite only bundles files reachable from `main.jsx`; `DecisionTrace` is not wired in yet, so this just confirms no syntax error in the touched CSS. (It is fine if `DecisionTrace` is tree-shaken out at this point.)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/DecisionTrace.jsx frontend/src/styles.css
git commit -m "feat(fe): DecisionTrace per-stock why card + styles"
```

---

### Task 3: Why view

**Files:**
- Create: `frontend/src/views/Why.jsx`

- [ ] **Step 1: Create the view**

Create `frontend/src/views/Why.jsx`:

```jsx
// "Why" view: a plain-English narrative of the run, then one DecisionTrace card
// per scanned stock (highest score first). When arriving from a Today row click,
// the matching card is expanded and scrolled into view.
import { useEffect, useRef } from 'react';
import { DataGate, Card } from '../components/ui.jsx';
import { runNarrative } from '../lib/narrative.js';
import DecisionTrace from '../components/DecisionTrace.jsx';

export default function Why({ report, focusSymbol }) {
  const focusRef = useRef(null);

  useEffect(() => {
    if (focusSymbol && focusRef.current) {
      focusRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [focusSymbol, report.data]);

  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const signals = (data.signals || [])
          .slice()
          .sort((a, b) => Number(b.score) - Number(a.score));
        const narrative = runNarrative(data);
        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Why</h2>
              <p>
                What the engine decided this run and the reasoning behind each call —
                straight from the strategies that scored every stock.
              </p>
            </div>

            <Card title="What the engine did" sub={`${data.checkpoint} checkpoint`}>
              <div className="card-pad stack" style={{ gap: 8 }}>
                {narrative.map((line, i) => (
                  <p key={i} className="muted" style={{ margin: 0 }}>
                    {line}
                  </p>
                ))}
              </div>
            </Card>

            <div className="stack" style={{ gap: 14 }}>
              {signals.map((s) => {
                const isFocus = focusSymbol != null && s.symbol === focusSymbol;
                return (
                  <div key={s.signal_id || s.symbol} ref={isFocus ? focusRef : null}>
                    <DecisionTrace signal={s} defaultOpen={isFocus} />
                  </div>
                );
              })}
            </div>
          </div>
        );
      }}
    </DataGate>
  );
}
```

- [ ] **Step 2: Commit** (build is exercised once App is wired in Task 6)

```bash
git add frontend/src/views/Why.jsx
git commit -m "feat(fe): Why view — narrative + per-stock decision traces"
```

---

### Task 4: Today view

**Files:**
- Create: `frontend/src/views/Today.jsx`

- [ ] **Step 1: Create the view**

Create `frontend/src/views/Today.jsx`:

```jsx
// "Today" view: the at-a-glance landing. Snapshot tiles, a one-line run headline,
// and the full list of calls. Clicking a call row jumps to Why for that stock.
import { useData } from '../hooks/useData.js';
import { DataGate, Card, Stat, Money, Pct, LabelPill, RiskPill } from '../components/ui.jsx';
import { formatINR, formatInt, formatScore, formatDateTime } from '../lib/format.js';
import { runHeadline } from '../lib/narrative.js';

function pct(part, whole) {
  const p = Number(part);
  const w = Number(whole);
  if (!w || Number.isNaN(p) || Number.isNaN(w)) return null;
  return (p / w) * 100;
}

export default function Today({ report, onSelectSymbol }) {
  const apiUsage = useData('api_usage.json');

  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const p = data.portfolio || {};
        const calls = (data.signals || [])
          .slice()
          .sort((a, b) => Number(b.score) - Number(a.score));
        const openPositions = (p.positions || []).length;
        const budgetUsedPct = pct(p.capital_deployed, p.monthly_capital);

        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Today</h2>
              <p>
                Generated {formatDateTime(data.generated_at)} ({data.checkpoint} checkpoint).
              </p>
            </div>

            <div className="callout info">
              <strong>{runHeadline(data)}</strong>
            </div>

            <div className="grid cols-4">
              <Stat
                label="Fake capital (total value)"
                value={formatINR(p.total_value)}
                meta={`Starting ${formatINR(p.starting_capital)}`}
              />
              <Stat
                label="Total P&L"
                value={<Money value={p.total_pnl} signed />}
                meta={<Pct value={p.total_return_pct} />}
              />
              <Stat
                label="Open positions"
                value={formatInt(openPositions)}
                meta={`${formatInt(p.buys_this_month)} / ${formatInt(p.max_buys_per_month)} buys this month`}
              />
              <Stat
                label="Capital remaining"
                value={formatINR(p.capital_remaining)}
                meta={
                  budgetUsedPct == null
                    ? `of ${formatINR(p.monthly_capital)}`
                    : `${budgetUsedPct.toFixed(1)}% used of ${formatINR(p.monthly_capital)}`
                }
              />
            </div>

            <Card title="Today’s calls" sub="Every stock scored this run — click a row to see why">
              {calls.length === 0 ? (
                <div className="card-pad muted small">No candidate signals in this run.</div>
              ) : (
                <div className="table-wrap">
                  <table className="data">
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Name</th>
                        <th className="num-cell">Score</th>
                        <th>Call</th>
                        <th>Risk</th>
                        <th>Why (short)</th>
                        <th className="num-cell">Last price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {calls.map((s) => (
                        <tr
                          key={s.signal_id || s.symbol}
                          className="clickable"
                          onClick={() => onSelectSymbol && onSelectSymbol(s.symbol)}
                        >
                          <td className="sym">
                            {s.symbol}
                            {s.exchange ? <span className="exch">{s.exchange}</span> : null}
                          </td>
                          <td className="muted">{s.name || '—'}</td>
                          <td className="num-cell">{formatScore(s.score)}</td>
                          <td>
                            <LabelPill label={s.label} />
                          </td>
                          <td>
                            <RiskPill risk={s.risk_level} />
                          </td>
                          <td className="muted small" style={{ maxWidth: 360 }}>
                            {s.reason || '—'}
                          </td>
                          <td className="num-cell">{formatINR(s.last_price)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        );
      }}
    </DataGate>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Today.jsx
git commit -m "feat(fe): Today view — snapshot, headline, clickable calls"
```

---

### Task 5: Track Record view

**Files:**
- Create: `frontend/src/views/TrackRecord.jsx`

- [ ] **Step 1: Create the view**

Create `frontend/src/views/TrackRecord.jsx`:

```jsx
// "Track Record" view: is the engine actually making good calls? Reuses the
// existing EvidenceSummary (maturity + decision edge) and BenchmarkComparison
// (vs the index), plus cost-adjusted realised P&L from the report.
import { useData } from '../hooks/useData.js';
import { DataGate, Card, Stat, Money } from '../components/ui.jsx';
import { formatInt } from '../lib/format.js';
import EvidenceSummary from '../components/EvidenceSummary.jsx';
import BenchmarkComparison from '../components/BenchmarkComparison.jsx';

export default function TrackRecord({ report }) {
  const dq = useData('decision_quality.json');

  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const cap = data.cost_adjusted_pnl || {};
        const dqData = dq.data && dq.data.enabled !== false ? dq.data : null;
        const evidence = dqData || data.decision_quality || null;

        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Track Record</h2>
              <p>
                Is the engine actually making good calls? Maturity, edge versus the index, and
                realised paper P&L — net of estimated Indian delivery costs.
              </p>
            </div>

            {evidence ? (
              <EvidenceSummary
                summary={evidence.evidence_summary}
                metrics={evidence.metrics}
                readiness={evidence.readiness}
              />
            ) : null}

            <Card
              title="Cost-adjusted realised P&L"
              sub="Net of estimated Indian delivery costs (brokerage, STT, fees, stamp duty)"
            >
              <div className="card-pad">
                <div className="grid cols-4">
                  <Stat label="Gross realised P&L" value={<Money value={cap.gross_realized_pnl} signed />} />
                  <Stat label="Estimated costs" value={<Money value={cap.estimated_costs} />} />
                  <Stat
                    label="Net realised (cost-adj.)"
                    value={<Money value={cap.net_realized_pnl_cost_adjusted} signed />}
                  />
                  <Stat
                    label="Win rate"
                    value={cap.win_rate_pct == null ? '—' : `${Number(cap.win_rate_pct).toFixed(1)}%`}
                    meta={`${formatInt(cap.closed_trades)} closed · ${formatInt(cap.wins)}W / ${formatInt(cap.losses)}L`}
                  />
                </div>
              </div>
            </Card>

            <BenchmarkComparison />
          </div>
        );
      }}
    </DataGate>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/TrackRecord.jsx
git commit -m "feat(fe): Track Record view — maturity, realised P&L, benchmark"
```

---

### Task 6: Rewire App to 3 views

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Replace App.jsx**

Replace the entire contents of `frontend/src/App.jsx` with:

```jsx
import { useState } from 'react';
import { useData } from './hooks/useData.js';
import { formatDateTime } from './lib/format.js';

import Today from './views/Today.jsx';
import Why from './views/Why.jsx';
import TrackRecord from './views/TrackRecord.jsx';

const TABS = [
  { id: 'today', label: 'Today' },
  { id: 'why', label: 'Why' },
  { id: 'track', label: 'Track Record' },
];

function PaperBanner() {
  return (
    <div className="paper-banner">
      <div className="container">
        <span className="dot" />
        <span>PAPER TRADING ONLY — fake money. Live trading DISABLED.</span>
      </div>
    </div>
  );
}

function StatusStrip({ report }) {
  const exec = report?.execution || {};
  const generatedAt = report?.generated_at;
  return (
    <div className="status-strip">
      <span className="status-item">
        <span className="status-led info" /> Mode = <b>PAPER</b>
      </span>
      <span className="status-item">
        <span className="status-led info" /> Broker adapter = <b>{exec.broker_adapter || 'paper'}</b>
      </span>
      <span className="status-item">
        <span className="status-led off" /> Live trading = <b>DISABLED</b>
      </span>
      <span className="status-item">
        <span className="status-led off" /> Angel One = <b>DISABLED</b>
      </span>
      <span className="status-item">
        <span className="status-led ok" /> Last updated ={' '}
        <b>{generatedAt ? formatDateTime(generatedAt) : '—'}</b>
      </span>
    </div>
  );
}

export default function App() {
  const [active, setActive] = useState('today');
  const [focusSymbol, setFocusSymbol] = useState(null);

  // The report is the spine of the dashboard; share it across views.
  const report = useData('latest_report.json');

  function goToWhy(symbol) {
    setFocusSymbol(symbol);
    setActive('why');
  }

  return (
    <div className="app-shell">
      <PaperBanner />

      <header className="app-header">
        <div className="container">
          <div className="brand">
            <div className="brand-mark">₹</div>
            <div>
              <h1>Paper Trading Desk</h1>
              <p>Indian equities · multi-strategy signal engine · fake-money demo</p>
            </div>
          </div>
          <StatusStrip report={report.data} />
        </div>
      </header>

      <nav className="tabs" aria-label="Sections">
        <div className="container">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`tab-btn ${active === t.id ? 'active' : ''}`}
              onClick={() => setActive(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="content">
        <div className="container">
          {active === 'today' && <Today report={report} onSelectSymbol={goToWhy} />}
          {active === 'why' && <Why report={report} focusSymbol={focusSymbol} />}
          {active === 'track' && <TrackRecord report={report} />}
        </div>
      </main>

      <footer className="app-footer">
        <div className="container">
          Demo dashboard. Numbers are simulated paper-trading results — no real orders are ever
          placed, no broker is connected, and no funds are at risk. Not investment advice.
        </div>
      </footer>
    </div>
  );
}
```

- [ ] **Step 2: Build the whole app**

Run (from `frontend/`): `npm run build`
Expected: build succeeds. Now `Today`, `Why`, `TrackRecord`, `DecisionTrace`, and `narrative.js` are all reachable from `App.jsx`, so any import-path or JSX error surfaces here. Fix and rebuild until green.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat(fe): collapse nav to 3 views (Today / Why / Track Record)"
```

---

### Task 7: Smoke test, clean up, open PR

**Files:** none (verification + git only)

- [ ] **Step 1: Re-run the narrative unit test (regression guard)**

Run (from `frontend/`): `node scripts/test_narrative.mjs`
Expected: `OK: narrative helpers pass`.

- [ ] **Step 2: Local preview smoke test**

Run (from `frontend/`): `npm run preview`
Open the printed local URL and verify:
- **Today**: 3 nav tabs only; headline callout renders; snapshot shows buys `X / 100`; clicking a calls row switches to **Why**.
- **Why**: narrative paragraph at top; one card per stock; the clicked stock's card is expanded and scrolled into view; "Show strategy votes" toggles the breakdown.
- **Track Record**: Evidence command center + cost-adjusted P&L + benchmark all render (or show graceful empty states).
Stop the preview server when done (Ctrl-C).

- [ ] **Step 3: Revert any demo-data files the build dirtied**

The `prebuild`/`predev` step runs `node scripts/copy-data.mjs`, which can rewrite committed JSON under `public/data/` (and `npm`/python runs can touch `data/`). Keep the diff source-only.

Run (from repo root `C:\Users\Mishael Abhishek\Projects\finance_mmg`):
```bash
git status --porcelain
git checkout -- public/data data 2>/dev/null || true
git status --porcelain
```
Expected after: only intended source files under `frontend/src`, `frontend/scripts`, and `docs/` appear (all already committed in Tasks 1–6); no stray `public/data/*` or `data/*` modifications remain.

- [ ] **Step 4: Push the branch and open a PR**

```bash
git push -u origin feature/simplified-xai-dashboard
gh pr create --base main --head feature/simplified-xai-dashboard \
  --title "Simplify dashboard to 3 views + XAI 'Why' decision traces" \
  --body "Collapses the 14-tab dashboard to Today / Why / Track Record. Adds an explainable-AI 'Why' view (run narrative + per-stock decision traces rendering the engine's own strategy votes/reasons). Frontend-only — no backend, config, or workflow change; safety posture (paper-only, live trading DISABLED) unchanged. Other components are archived (kept in repo, dropped from nav). Spec + plan under docs/superpowers/."
```

- [ ] **Step 5: Stop. Do not merge.** Report the PR URL and the verification results to the user; merging is the user's call.

---

## Self-Review

**Spec coverage:**
- 14→3 nav — Task 6. ✓
- Today (snapshot + headline + clickable calls) — Task 4. ✓
- Why (narrative + per-stock traces, focus on click) — Tasks 1, 2, 3. ✓
- Track Record (maturity + benchmark + cost-adj P&L) — Task 5. ✓
- New files `narrative.js`, `DecisionTrace.jsx`, 3 views — Tasks 1–5. ✓
- Reuse `EvidenceSummary`/`BenchmarkComparison`/`StrategyBreakdown`/`ui`/`format` — Tasks 2, 3, 5. ✓
- Archive (no deletes) — Task 6 drops imports only; no `git rm`. ✓
- Cross-view linking via `{activeView, focusSymbol}` — Task 6. ✓
- No backend/config/workflow change — confirmed: only `frontend/` + `docs/` touched. ✓
- Verification: `npm run build` + preview + revert dirtied data — Tasks 6, 7. ✓

**Placeholder scan:** none — every step has full file content or exact commands.

**Type consistency:** `summarizeRun`/`runHeadline`/`runNarrative`/`orderStrategyVotes` names match between `narrative.js`, the test, `DecisionTrace`, `Why`, and `Today`. `onSelectSymbol` (Today) ↔ `goToWhy` (App). `focusSymbol` prop (Why) ↔ App state. `report` (a `useData` result with `.data`/`.loading`/`.error`) passed uniformly into every view's `DataGate`. ✓
