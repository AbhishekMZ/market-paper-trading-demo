// News events — the raw news items pulled this run (newest first), with
// per-item sentiment, risk level, and detected event types.
import { useData } from '../hooks/useData.js';
import { Card, Pill, DataGate } from './ui.jsx';
import { formatDateTime } from '../lib/format.js';

function riskTone(level) {
  if (level === 'CRITICAL' || level === 'HIGH') return 'neg';
  if (level === 'MEDIUM') return 'warn';
  if (level === 'LOW') return 'info';
  return 'neutral';
}

function sentimentTone(sentiment) {
  if (sentiment === 'NEGATIVE') return 'neg';
  if (sentiment === 'POSITIVE') return 'ok';
  return 'neutral';
}

function whenLabel(item) {
  if (item.published_at) return formatDateTime(item.published_at);
  if (item.age_hours != null) return `${item.age_hours}h ago`;
  return '—';
}

export default function NewsEvents() {
  const items = useData('news_items.json');

  return (
    <div className="grid">
      <Card title="News events" sub="Headlines pulled this run (newest first)">
        <DataGate
          file="news_items.json"
          state={items}
          emptyWhen={(d) => !Array.isArray(d) || d.length === 0}
        >
          {(rows) => (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>When</th>
                    <th>Symbol</th>
                    <th>Source</th>
                    <th>Headline</th>
                    <th>Risk</th>
                    <th>Sentiment</th>
                    <th>Events</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={i}>
                      <td className="mono small">{whenLabel(r)}</td>
                      <td>{r.symbol}</td>
                      <td className="small">
                        {r.source}
                        {r.provider ? <span className="dim small"> {r.provider}</span> : null}
                      </td>
                      <td className="small">
                        {r.url ? (
                          <a href={r.url} target="_blank" rel="noreferrer">{r.title}</a>
                        ) : (
                          r.title
                        )}
                      </td>
                      <td><Pill tone={riskTone(r.risk_level)}>{r.risk_level || '—'}</Pill></td>
                      <td><Pill tone={sentimentTone(r.sentiment)}>{r.sentiment || '—'}</Pill></td>
                      <td className="small">{(r.event_types && r.event_types.join(', ')) || '—'}</td>
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
