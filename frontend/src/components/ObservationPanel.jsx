// Observation Panel — lightweight between-checkpoint monitoring summary plus
// the latest critical trigger from the observation & escalation engine.
import { useData } from '../hooks/useData.js';
import { Card, Stat, DataGate } from './ui.jsx';
import { formatDateTime } from '../lib/format.js';

export default function ObservationPanel() {
  const report = useData('observation_report.json');
  const triggers = useData('trigger_history.json');

  return (
    <Card title="Observation" sub="Lightweight between-checkpoint monitoring (paper-only)">
      <DataGate file="observation_report.json" state={report}>
        {(r) => {
          const m = r.metrics || {};
          const blocked = r.blocked_actions?.length ?? 0;
          return (
            <>
              <div className="stat-row">
                <Stat label="Mode" value={r.mode || '—'} />
                <Stat label="Last observation" value={formatDateTime(m.last_run || r.as_of)} />
                <Stat label="Watchlist size" value={r.watchlist_size ?? 0} />
                <Stat label="Open positions observed" value={r.open_positions_observed?.length ?? r.observed ?? 0} />
                <Stat label="Triggers" value={m.triggers_detected ?? r.triggers_this_run ?? 0} />
                <Stat label="Escalations pending" value={r.escalations ?? 0} />
                <Stat label="Actions blocked" value={blocked} tone={blocked > 0 ? 'neg' : ''} />
              </div>
              <DataGate file="trigger_history.json" state={triggers}>
                {(rows) => {
                  const crit = Array.isArray(rows)
                    ? rows.find((t) => t.severity === 'CRITICAL')
                    : null;
                  return (
                    <div className="muted small" style={{ marginTop: 8 }}>
                      Latest critical trigger: {crit ? `${crit.symbol} — ${crit.reason}` : 'none'}
                    </div>
                  );
                }}
              </DataGate>
            </>
          );
        }}
      </DataGate>
    </Card>
  );
}
