import { Card, Stat, Pill } from './ui.jsx';
import { formatInt, formatPct } from '../lib/format.js';

function readinessTone(value) {
  if (value === 'EARLY_PROMISING' || value === 'ok') return 'ok';
  if (value === 'EARLY_WEAK' || value === 'warn') return 'warn';
  return 'neutral';
}

function progressPct(item) {
  const current = Number(item?.current || 0);
  const required = Number(item?.required || 0);
  if (!required) return item?.done ? 100 : 0;
  return Math.min((current / required) * 100, 100);
}

export default function EvidenceSummary({ summary, metrics, readiness }) {
  const s = summary || {};
  const m = metrics || {};
  const r = readiness || {};
  const checks = Array.isArray(s.maturity_checks) ? s.maturity_checks : [];
  const takeaways = Array.isArray(s.takeaways) ? s.takeaways : [];
  const watchItems = Array.isArray(s.watch_items) ? s.watch_items : [];
  const status = s.status || r.verdict || 'COLLECTING_EVIDENCE';
  const score = Number(s.evidence_score || 0);

  return (
    <Card
      title="Evidence command center"
      sub="Decision-quality maturity, edge, and next review points in one place"
      headRight={<Pill tone={readinessTone(s.tone || status)}>{status}</Pill>}
    >
      <div className="card-pad stack">
        <div className={`callout ${readinessTone(s.tone || status)}`}>
          <strong>{s.headline || 'Collecting paper-trading evidence.'}</strong>
          <div className="small muted" style={{ marginTop: 6 }}>
            Live trading: {s.live_trading || r.live_trading || 'DISABLED'} · Auto-tuning: {s.auto_tuning || 'DISABLED'}
          </div>
        </div>

        <div className="grid cols-4">
          <Stat label="Evidence maturity" value={formatPct(score, 1)} meta="configured minimum sample" />
          <Stat label="Tracked episodes" value={formatInt(m.total_tracked_episodes ?? r.progress?.tracked_episodes)} meta={`${formatInt(m.matured_episodes)} matured`} />
          <Stat label="Paper trades" value={formatInt(m.paper_trades ?? r.progress?.paper_trades)} meta="filled paper orders" />
          <Stat label="Decision edge" value={formatPct(m.decision_edge_pct, 2)} tone={Number(m.decision_edge_pct || 0) > 0 ? 'pos' : Number(m.decision_edge_pct || 0) < 0 ? 'neg' : 'zero'} meta="acted vs declined" />
        </div>

        {checks.length > 0 ? (
          <div className="evidence-grid">
            {checks.map((item) => (
              <div className="evidence-check" key={item.label}>
                <div className="row between">
                  <strong>{item.label}</strong>
                  <span className={item.done ? 'pos small' : 'muted small'}>
                    {formatInt(item.current)} / {formatInt(item.required)}
                  </span>
                </div>
                <div className="progress-track">
                  <div className={item.done ? 'progress-fill ok' : 'progress-fill'} style={{ width: `${progressPct(item)}%` }} />
                </div>
              </div>
            ))}
          </div>
        ) : null}

        <div className="grid cols-2">
          <div>
            <div className="section-label">What the evidence says</div>
            <ul className="bullets">
              {takeaways.length ? takeaways.map((item, i) => (
                <li key={i}><span className="ic">•</span><span>{item}</span></li>
              )) : <li><span className="ic">•</span><span>Evidence summary will appear after the next analyzer run.</span></li>}
            </ul>
          </div>
          <div>
            <div className="section-label">What to watch next</div>
            <ul className="bullets">
              {watchItems.length ? watchItems.map((item, i) => (
                <li key={i}><span className="ic">•</span><span>{item}</span></li>
              )) : <li><span className="ic">•</span><span>Keep paper mode running until readiness requirements are met.</span></li>}
            </ul>
          </div>
        </div>
      </div>
    </Card>
  );
}
