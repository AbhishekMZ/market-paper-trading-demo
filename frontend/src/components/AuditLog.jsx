import { useState, useMemo } from 'react';
import { useData } from '../hooks/useData.js';
import { Card, DataGate, LabelPill, RiskPill } from './ui.jsx';
import { formatDateTime, formatScore, formatINR } from '../lib/format.js';

function EventPill({ event }) {
  const e = String(event || '').toUpperCase();
  let tone = 'neutral';
  if (e.includes('FILLED') || e.includes('BUY')) tone = 'buy';
  else if (e.includes('SELL') || e.includes('REJECT') || e.includes('EXIT')) tone = 'danger';
  else if (e.includes('EMAIL')) tone = 'watch';
  else if (e.includes('EVALUATED')) tone = 'review';
  return <span className={`pill ${tone}`}>{event || 'EVENT'}</span>;
}

function Field({ label, children }) {
  if (children == null || children === '' || children === '—') return null;
  return (
    <div className="row" style={{ gap: 6, alignItems: 'baseline' }}>
      <span className="dim small" style={{ minWidth: 130 }}>
        {label}
      </span>
      <span className="small">{children}</span>
    </div>
  );
}

function AuditEntry({ e }) {
  const warnings = e.warnings || [];
  const conflicts = e.conflicts || [];
  return (
    <div className="card" style={{ background: 'var(--surface-2)' }}>
      <div className="card-pad stack" style={{ gap: 8 }}>
        <div className="row between">
          <div className="row" style={{ gap: 10 }}>
            <EventPill event={e.event} />
            {e.symbol ? <span className="sym">{e.symbol}</span> : null}
            {e.final_recommendation ? <LabelPill label={e.final_recommendation} /> : null}
            {e.risk_level ? <RiskPill risk={e.risk_level} /> : null}
          </div>
          <span className="dim small" style={{ whiteSpace: 'nowrap' }}>
            {formatDateTime(e.ts)}
          </span>
        </div>

        {e.reason || e.message ? (
          <p className="muted small" style={{ margin: 0 }}>
            {e.reason || e.message}
          </p>
        ) : null}

        <div className="grid cols-2" style={{ gap: 4 }}>
          <Field label="Market regime">{e.market_regime}</Field>
          <Field label="Final score">
            {e.final_score != null ? formatScore(e.final_score) : null}
          </Field>
          <Field label="Decision taken">{e.decision_taken}</Field>
          <Field label="Paper order">
            {e.paper_order_created === true
              ? 'created'
              : e.paper_order_created === false
                ? 'not created'
                : null}
          </Field>
          <Field label="Broker adapter">{e.broker_adapter}</Field>
          <Field label="Execution mode">{e.execution_mode || e.mode}</Field>
          <Field label="Estimated costs">
            {e.estimated_costs != null ? formatINR(e.estimated_costs) : null}
          </Field>
          <Field label="Data quality">{e.data_quality_status}</Field>
          <Field label="Order id">{e.order_id ? <span className="mono">{e.order_id}</span> : null}</Field>
        </div>

        {warnings.length > 0 ? (
          <div className="callout warn" style={{ padding: '8px 12px' }}>
            <ul className="clean small" style={{ margin: 0 }}>
              {warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {conflicts.length > 0 ? (
          <div className="callout danger" style={{ padding: '8px 12px' }}>
            <ul className="clean small" style={{ margin: 0 }}>
              {conflicts.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function AuditLog() {
  const audit = useData('audit_log.json');
  const [q, setQ] = useState('');

  return (
    <DataGate file="audit_log.json" state={audit}>
      {(data) => {
        const rows = Array.isArray(data) ? data : [];
        return <AuditList rows={rows} q={q} setQ={setQ} />;
      }}
    </DataGate>
  );
}

function AuditList({ rows, q, setQ }) {
  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter((e) => {
      const hay = `${e.symbol || ''} ${e.event || ''} ${e.final_recommendation || ''} ${
        e.reason || e.message || ''
      }`.toLowerCase();
      return hay.includes(needle);
    });
  }, [rows, q]);

  return (
    <div className="stack">
      <div className="view-head">
        <h2>Audit Log</h2>
        <p>
          A defensive, append-only record of every decision (newest first). Some entries
          (emails, fills) carry fewer fields — those are rendered as available.
        </p>
      </div>

      <Card
        title={`${filtered.length} of ${rows.length} entries`}
        headRight={
          <input
            className="input"
            placeholder="Filter by symbol or event…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        }
      >
        <div className="card-pad stack" style={{ gap: 10 }}>
          {filtered.length === 0 ? (
            <div className="muted small">No matching audit entries.</div>
          ) : (
            filtered.map((e, i) => <AuditEntry key={`${e.ts}-${i}`} e={e} />)
          )}
        </div>
      </Card>
    </div>
  );
}
