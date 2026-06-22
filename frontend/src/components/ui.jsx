// Small shared UI primitives used across views.
import {
  labelMeta,
  riskMeta,
  regimeMeta,
  formatINR,
  pnlSign,
  formatPct,
} from '../lib/format.js';

export function Pill({ tone = 'neutral', children }) {
  return <span className={`pill ${tone}`}>{children}</span>;
}

export function LabelPill({ label }) {
  const m = labelMeta(label);
  return <Pill tone={m.tone}>{m.text}</Pill>;
}

export function RiskPill({ risk }) {
  const m = riskMeta(risk);
  return <Pill tone={m.tone}>{m.text}</Pill>;
}

export function RegimePill({ regime }) {
  const m = regimeMeta(regime);
  return <Pill tone={m.tone}>{m.text}</Pill>;
}

/** Money colored by sign. */
export function Money({ value, signed = false }) {
  const sign = pnlSign(value);
  const cls = signed ? sign : '';
  return <span className={`num ${cls}`}>{formatINR(value)}</span>;
}

/** Percent colored by sign. */
export function Pct({ value, digits = 2 }) {
  const sign = pnlSign(value);
  return <span className={`num ${sign}`}>{formatPct(value, digits)}</span>;
}

export function Loading({ label = 'Loading data…' }) {
  return (
    <div className="state">
      <div className="spinner" />
      <div className="muted small">{label}</div>
    </div>
  );
}

export function ErrorState({ file, error }) {
  return (
    <div className="state">
      <div className="ttl">Data unavailable</div>
      <div className="muted small">
        Couldn’t load <code className="mono">{file}</code>.
      </div>
      {error ? <div className="dim small">{error}</div> : null}
      <div className="dim small">
        This is a static demo — the file may not have been generated yet. The rest of the
        dashboard still works.
      </div>
    </div>
  );
}

export function Empty({ children = 'Nothing to show yet.' }) {
  return (
    <div className="state">
      <div className="muted small">{children}</div>
    </div>
  );
}

/**
 * Wrap a useData() result. Renders loading / error / empty placeholders so a
 * missing file never crashes the page. `children` receives the data.
 */
export function DataGate({ file, state, children, emptyWhen }) {
  if (state.loading) return <Loading />;
  if (state.error || state.data == null) return <ErrorState file={file} error={state.error} />;
  if (typeof emptyWhen === 'function' && emptyWhen(state.data)) {
    return <Empty />;
  }
  return children(state.data);
}

export function Card({ title, sub, children, headRight, pad = false }) {
  return (
    <section className="card">
      {title ? (
        <div className="card-head">
          <div>
            <h3>{title}</h3>
            {sub ? <div className="sub">{sub}</div> : null}
          </div>
          {headRight || null}
        </div>
      ) : null}
      <div className={pad ? 'card-pad' : ''}>{children}</div>
    </section>
  );
}

export function Stat({ label, value, meta, tone }) {
  return (
    <div className="stat">
      <div className="label">{label}</div>
      <div className={`value ${tone || ''}`}>{value}</div>
      {meta ? <div className="meta">{meta}</div> : null}
    </div>
  );
}
