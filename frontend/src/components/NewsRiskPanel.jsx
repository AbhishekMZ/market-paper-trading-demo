// News Risk — overall news-risk posture for this run plus a per-symbol
// breakdown (sentiment, risk level, and whether news blocks a paper buy).
import { useData } from '../hooks/useData.js';
import { Card, Stat, Pill, DataGate } from './ui.jsx';
import { formatDateTime } from '../lib/format.js';

function overallTone(overall) {
  if (overall === 'CRITICAL') return 'neg';
  if (overall === 'ELEVATED') return 'warn';
  if (overall === 'NORMAL') return 'ok';
  return 'neutral';
}

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

export default function NewsRiskPanel() {
  const health = useData('news_health.json');
  const assessments = useData('news_assessments.json');

  return (
    <div className="grid">
      <Card title="News Risk" sub="Adverse-news posture for this run">
        <DataGate file="news_health.json" state={health}>
          {(h) => (
            <>
              <div className="stat-row">
                <Stat
                  label="Overall"
                  value={<Pill tone={overallTone(h.overall)}>{h.overall || '—'}</Pill>}
                />
                <Stat label="Symbols with news" value={h.symbols_with_news ?? 0} />
                <Stat label="Blocked buys" value={h.blocked_buys ?? 0} tone={h.blocked_buys ? 'neg' : ''} />
                <Stat label="Critical" value={h.critical_count ?? 0} tone={h.critical_count ? 'neg' : ''} />
                <Stat label="High" value={h.high_count ?? 0} />
                <Stat label="Last run" value={h.last_run ? formatDateTime(h.last_run) : '—'} />
              </div>
            </>
          )}
        </DataGate>
      </Card>

      <Card title="Per-symbol news" sub="Symbols with news this run (newest assessment)">
        <DataGate
          file="news_assessments.json"
          state={assessments}
          emptyWhen={(d) => !Array.isArray(d) || d.filter((r) => r.news_available).length === 0}
        >
          {(rows) => (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Risk</th>
                    <th>Sentiment</th>
                    <th>Blocks buy</th>
                    <th>Items</th>
                    <th>Top headline</th>
                  </tr>
                </thead>
                <tbody>
                  {rows
                    .filter((r) => r.news_available)
                    .map((r, i) => (
                      <tr key={i}>
                        <td>{r.symbol}</td>
                        <td><Pill tone={riskTone(r.news_risk_level)}>{r.news_risk_level || '—'}</Pill></td>
                        <td><Pill tone={sentimentTone(r.overall_sentiment)}>{r.overall_sentiment || '—'}</Pill></td>
                        <td>
                          {r.blocks_buy ? <Pill tone="neg">YES</Pill> : <span className="dim small">no</span>}
                        </td>
                        <td className="mono small">{r.item_count ?? 0}</td>
                        <td className="small">{(r.top_items && r.top_items[0]?.title) || '—'}</td>
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
