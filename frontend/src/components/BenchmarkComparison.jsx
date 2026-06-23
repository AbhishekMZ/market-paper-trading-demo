// Benchmark comparison — the paper portfolio versus the index (NIFTY 50), with
// a short history of the equity curve when enough data exists.
import { useData } from '../hooks/useData.js';
import { Card, Stat, Pill, DataGate } from './ui.jsx';

// Return tinting: a number > 0 => 'pos', < 0 => 'neg', else ''.
function returnTone(value) {
  const n = Number(value);
  if (value === null || value === undefined || Number.isNaN(n) || n === 0) return '';
  return n > 0 ? 'pos' : 'neg';
}

function verdictTone(verdict) {
  if (verdict === 'AHEAD') return 'ok';
  if (verdict === 'BEHIND') return 'neg';
  return 'neutral';
}

export default function BenchmarkComparison() {
  const dq = useData('decision_quality.json');

  return (
    <Card title="Benchmark comparison" sub="Paper portfolio vs the index">
      <DataGate
        file="decision_quality.json"
        state={dq}
        emptyWhen={(d) => !d || d.enabled === false || d.benchmark?.ready === false}
      >
        {(d) => {
          const b = d.benchmark || {};
          const history = Array.isArray(b.history) ? b.history.slice(-10) : [];
          return (
            <>
              <div className="stat-row">
                <Stat label="Benchmark" value={b.benchmark_name || '—'} />
                <Stat
                  label="Portfolio return %"
                  value={b.portfolio_return_pct ?? 0}
                  tone={returnTone(b.portfolio_return_pct)}
                />
                <Stat
                  label={`${b.benchmark_name || 'Benchmark'} return %`}
                  value={b.benchmark_return_pct ?? 0}
                  tone={returnTone(b.benchmark_return_pct)}
                />
                <Stat
                  label="Outperformance %"
                  value={b.outperformance_pct ?? 0}
                  tone={returnTone(b.outperformance_pct)}
                />
                <Stat
                  label="Verdict"
                  value={<Pill tone={verdictTone(b.verdict)}>{b.verdict}</Pill>}
                />
                <Stat label="Window" value={`${b.from_date} → ${b.to_date}`} />
                <Stat label="Points" value={b.points ?? 0} />
              </div>
              {history.length > 0 ? (
                <div className="table-wrap" style={{ marginTop: 8 }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>NIFTY close</th>
                        <th>Portfolio total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((h, i) => (
                        <tr key={i}>
                          <td className="mono small">{h.date}</td>
                          <td className="mono small">{h.nifty_close}</td>
                          <td className="mono small">{h.portfolio_total}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </>
          );
        }}
      </DataGate>
    </Card>
  );
}
