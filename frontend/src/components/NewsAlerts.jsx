// News alerts — adverse-news email alerts sent this month. These flag risk
// only; they never place a trade.
import { useData } from '../hooks/useData.js';
import { Card, Pill, DataGate } from './ui.jsx';
import { formatDateTime } from '../lib/format.js';

function levelTone(level) {
  if (level === 'CRITICAL') return 'neg';
  if (level === 'HIGH') return 'warn';
  return 'neutral';
}

export default function NewsAlerts() {
  const alerts = useData('news_alerts.json');

  return (
    <div className="grid">
      <Card title="News alerts (email)" sub="Adverse-news alerts sent this month (paper-only)">
        <DataGate
          file="news_alerts.json"
          state={alerts}
          emptyWhen={(d) => !Array.isArray(d) || d.length === 0}
        >
          {(rows) => (
            <>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Symbol</th>
                      <th>Level</th>
                      <th>Subject</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={i}>
                        <td className="mono small">{formatDateTime(r.ts)}</td>
                        <td>{r.symbol}</td>
                        <td><Pill tone={levelTone(r.level)}>{r.level || '—'}</Pill></td>
                        <td className="small">{r.subject}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="muted small" style={{ marginTop: 8 }}>
                Email is the only alert channel. News alerts never place a trade — they flag risk.
              </div>
            </>
          )}
        </DataGate>
      </Card>
    </div>
  );
}
