// Active Watchlist — the symbols the observer is actively watching between
// checkpoints (a focused subset, not the full universe).
import { useData } from '../hooks/useData.js';
import { Card, Pill, DataGate } from './ui.jsx';
import { formatDateTime } from '../lib/format.js';

function priorityTone(p) {
  if (p === 'HIGHEST') return 'neg';
  if (p === 'HIGH') return 'warn';
  if (p === 'MEDIUM') return 'info';
  return 'neutral';
}

export default function ActiveWatchlist() {
  const watchlist = useData('active_watchlist.json');

  return (
    <Card title="Active watchlist" sub="What the observer is watching (not the full universe)">
      <DataGate
        file="active_watchlist.json"
        state={watchlist}
        emptyWhen={(d) => !Array.isArray(d) || d.length === 0}
      >
        {(rows) => (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Reason</th>
                  <th>Priority</th>
                  <th>Last price</th>
                  <th>Trigger levels</th>
                  <th>Last signal</th>
                  <th>Expires</th>
                  <th>Open?</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => {
                  const levels = r.trigger_levels && Object.keys(r.trigger_levels).length > 0;
                  return (
                    <tr key={i}>
                      <td>{r.symbol}</td>
                      <td>{r.reason_added}</td>
                      <td><Pill tone={priorityTone(r.priority)}>{r.priority || '—'}</Pill></td>
                      <td>{r.last_price ?? '—'}</td>
                      <td className="mono small">{levels ? JSON.stringify(r.trigger_levels) : '—'}</td>
                      <td>{r.last_signal_label ?? '—'}</td>
                      <td className="mono small">{formatDateTime(r.expires_at)}</td>
                      <td>{r.is_open_position ? <Pill tone="info">yes</Pill> : <span className="dim">no</span>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </DataGate>
    </Card>
  );
}
