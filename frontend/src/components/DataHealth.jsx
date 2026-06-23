// Data Health — provider status, usable/rejected symbol counts, and the
// data-quality incident log (price anomalies, stale quotes, rejected marks).
import { useData } from '../hooks/useData.js';
import { Card, Stat, Pill, DataGate } from './ui.jsx';
import { formatDateTime } from '../lib/format.js';

function overallTone(overall) {
  if (overall === 'HEALTHY') return 'ok';
  if (overall === 'DEGRADED' || overall === 'NO_USABLE_DATA' || overall === 'STALE') return 'warn';
  return 'neutral';
}

export default function DataHealth() {
  const health = useData('data_health.json');
  const incidents = useData('data_quality_incidents.json');

  return (
    <div className="grid">
      <Card title="Data Health" sub="Quality of the market data feeding the engine">
        <DataGate file="data_health.json" state={health}>
          {(h) => (
            <>
              <div className="stat-row">
                <Stat label="Provider" value={h.provider || '—'} />
                <Stat
                  label="Overall"
                  value={<Pill tone={overallTone(h.overall)}>{h.overall || '—'}</Pill>}
                />
                <Stat label="Symbols assessed" value={h.symbols_assessed ?? 0} />
                <Stat label="Usable" value={h.usable_symbols ?? 0} tone="pos" />
                <Stat label="Rejected" value={h.rejected_symbols ?? 0} tone={h.rejected_symbols ? 'neg' : ''} />
              </div>
              <div className="stat-row">
                <Stat label="Price anomalies" value={h.price_anomalies ?? 0} tone={h.price_anomalies ? 'neg' : ''} />
                <Stat label="Stale quotes" value={h.stale_quotes ?? 0} />
                <Stat label="Missing news" value={h.missing_news ?? 0} />
                <Stat label="Rejected marks" value={h.mtm_incidents ?? 0} tone={h.mtm_incidents ? 'neg' : ''} />
                <Stat label="Last run" value={h.last_successful_run ? formatDateTime(h.last_successful_run) : '—'} />
              </div>
              {Array.isArray(h.anomaly_symbols) && h.anomaly_symbols.length > 0 ? (
                <div className="muted small" style={{ marginTop: 8 }}>
                  Anomaly symbols: {h.anomaly_symbols.join(', ')}
                </div>
              ) : null}
            </>
          )}
        </DataGate>
      </Card>

      <Card title="Data-quality incidents" sub="Blocked buys & rejected marks (newest first)">
        <DataGate
          file="data_quality_incidents.json"
          state={incidents}
          emptyWhen={(d) => !Array.isArray(d) || d.length === 0}
        >
          {(rows) => (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Symbol</th>
                    <th>Issue</th>
                    <th>Entry / Mark</th>
                    <th>Flags</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={i}>
                      <td className="mono small">{formatDateTime(r.ts)}</td>
                      <td>{r.symbol}</td>
                      <td><Pill tone="warn">{r.issue}</Pill></td>
                      <td className="mono small">
                        {r.entry_price ?? r.prev_price ?? '—'} → {r.mtm_price ?? r.rejected_price ?? '—'}
                        {r.jump_pct != null ? ` (${r.jump_pct}%)` : ''}
                      </td>
                      <td className="small">
                        {(r.anomaly_flags && r.anomaly_flags.join(', ')) || r.price_consistency_check || '—'}
                      </td>
                      <td className="small dim">{r.action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </DataGate>
      </Card>
    </div>
  );
}
