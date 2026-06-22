// Formatting + color-mapping helpers shared across the dashboard.

const inrFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const numberFormatter = new Intl.NumberFormat('en-IN', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

/** Money in ₹ with thousands separators and 2 decimals. */
export function formatINR(value) {
  const n = Number(value);
  if (value === null || value === undefined || Number.isNaN(n)) return '—';
  return inrFormatter.format(n);
}

/** Plain integer with Indian-style grouping. */
export function formatInt(value) {
  const n = Number(value);
  if (value === null || value === undefined || Number.isNaN(n)) return '—';
  return numberFormatter.format(n);
}

/** Percent with sign and fixed decimals, e.g. +2.50%. */
export function formatPct(value, digits = 2) {
  const n = Number(value);
  if (value === null || value === undefined || Number.isNaN(n)) return '—';
  const sign = n > 0 ? '+' : '';
  return `${sign}${n.toFixed(digits)}%`;
}

/** Score 0–100 with one decimal. */
export function formatScore(value) {
  const n = Number(value);
  if (value === null || value === undefined || Number.isNaN(n)) return '—';
  return n.toFixed(1);
}

/** Confidence (0..1) rendered as a percent, e.g. 0.65 -> 65%. */
export function formatConfidence(value) {
  const n = Number(value);
  if (value === null || value === undefined || Number.isNaN(n)) return '—';
  return `${Math.round(n * 100)}%`;
}

/** Human-friendly date+time from an ISO string. Falls back to the raw string. */
export function formatDateTime(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });
}

/** Short date only. */
export function formatDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

/** Sign of a P&L number: 'pos' | 'neg' | 'zero'. */
export function pnlSign(value) {
  const n = Number(value);
  if (Number.isNaN(n) || n === 0) return 'zero';
  return n > 0 ? 'pos' : 'neg';
}

// --- Label / regime / risk color maps -------------------------------------
// Each maps to a CSS class suffix used by the .pill component in styles.css.

export const LABEL_META = {
  BUY_SMALL_PAPER: { text: 'BUY SMALL (paper)', tone: 'buy' },
  WATCH: { text: 'WATCH', tone: 'watch' },
  HOLD: { text: 'HOLD', tone: 'hold' },
  NO_ACTION: { text: 'NO ACTION', tone: 'neutral' },
  DO_NOT_BUY: { text: 'DO NOT BUY', tone: 'danger' },
  HIGH_RISK_IGNORE: { text: 'HIGH RISK · IGNORE', tone: 'danger' },
  MANUAL_REVIEW: { text: 'MANUAL REVIEW', tone: 'review' },
  SELL_REVIEW: { text: 'SELL REVIEW', tone: 'review' },
  TRIM_REVIEW: { text: 'TRIM REVIEW', tone: 'review' },
  EXIT_REVIEW: { text: 'EXIT REVIEW', tone: 'review' },
};

export function labelMeta(label) {
  return LABEL_META[label] || { text: label || '—', tone: 'neutral' };
}

export const RISK_META = {
  LOW: { text: 'LOW', tone: 'risk-low' },
  MEDIUM: { text: 'MEDIUM', tone: 'risk-med' },
  HIGH: { text: 'HIGH', tone: 'risk-high' },
};

export function riskMeta(risk) {
  return RISK_META[risk] || { text: risk || '—', tone: 'neutral' };
}

export const REGIME_META = {
  RISK_ON: {
    text: 'RISK ON',
    tone: 'regime-on',
    blurb: 'Broad market strength. New paper buys are permitted (subject to per-signal risk checks).',
  },
  NEUTRAL: {
    text: 'NEUTRAL',
    tone: 'regime-neutral',
    blurb: 'No clear directional edge. Buys allowed but the bar for conviction is higher.',
  },
  RISK_OFF: {
    text: 'RISK OFF',
    tone: 'regime-off',
    blurb: 'Defensive conditions. New buys are throttled or blocked to protect capital.',
  },
  EVENT_RISK: {
    text: 'EVENT RISK',
    tone: 'regime-event',
    blurb: 'A known event raises uncertainty. New buys are blocked until it clears.',
  },
  DATA_INSUFFICIENT: {
    text: 'DATA INSUFFICIENT',
    tone: 'regime-data',
    blurb: 'Not enough reliable data to judge the regime. The system stays on the sidelines.',
  },
};

export function regimeMeta(regime) {
  return (
    REGIME_META[regime] || {
      text: regime || '—',
      tone: 'regime-neutral',
      blurb: 'Unrecognised regime label.',
    }
  );
}

/** Strategy signal direction -> tone (POSITIVE/NEGATIVE/NEUTRAL). */
export function signalTone(signal) {
  const s = String(signal || '').toUpperCase();
  if (s === 'POSITIVE') return 'pos';
  if (s === 'NEGATIVE') return 'neg';
  return 'zero';
}

/** Pretty-print a strategy_name like 'news_event_risk' -> 'News Event Risk'. */
export function humanizeKey(key) {
  if (!key) return '';
  return String(key)
    .split(/[_\s]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}
