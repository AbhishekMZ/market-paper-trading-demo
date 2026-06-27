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
