// Trigger History — meaningful changes the observer detected between
// checkpoints (price moves, regime shifts, etc.), newest first.
import { useData } from '../hooks/useData.js';
import { Card, Pill, DataGate } from './ui.jsx';
import { formatDateTime } from '../lib/format.js';

function severityTone(s) {
  if (s === 'CRITICAL' || s === 'HIGH') return 'neg';
  if (s === 'MEDIUM') return 'warn';
  if (s === 'LOW') return 'info';
  return 'neutral';
}

export default function TriggerHistory() {
  const triggers = useData('trigger_history.json');

  return (
    <Card title="Trigger history" sub="Meaningful changes detected between checkpoints">
      <DataGate
        file="trigger_history.json"
        state={triggers}
        emptyWhen={(d) => !Array.isArray(d) || d.length === 0}
      >
        {(rows) => (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Symbol</th>
                  <th>Trigger</th>
                  <th>Severity</th>
                  <th>Price</th>
                  <th>Change</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Next step</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 100).map((r, i) => (
                  <tr key={i}>
                    <td className="mono small">{formatDateTime(r.detected_at)}</td>
                    <td>{r.symbol}</td>
                    <td>{r.trigger_type}</td>
                    <td><Pill tone={severityTone(r.severity)}>{r.severity || '—'}</Pill></td>
                    <td>{r.price_at_detection ?? '—'}</td>
                    <td>{r.change_pct != null ? `${r.change_pct}%` : '—'}</td>
                    <td>{r.reason}</td>
                    <td>{r.status}</td>
                    <td className="small dim">{r.recommended_next_step}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </DataGate>
    </Card>
  );
}
