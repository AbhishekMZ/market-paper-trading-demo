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
