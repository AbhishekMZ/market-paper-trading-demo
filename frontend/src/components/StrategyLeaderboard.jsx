// Strategy leaderboard — ranks contributing signals by the average forward
// return of the episodes they appeared in. Indicative attribution, small sample.
import { useData } from '../hooks/useData.js';
import { Card, DataGate } from './ui.jsx';

// Return tinting: a number > 0 => 'pos', < 0 => 'neg', else ''.
function returnTone(value) {
  const n = Number(value);
  if (value === null || value === undefined || Number.isNaN(n) || n === 0) return '';
  return n > 0 ? 'pos' : 'neg';
}

export default function StrategyLeaderboard() {
  const dq = useData('decision_quality.json');

  return (
    <Card title="Strategy leaderboard" sub="By average forward return of contributing signals">
      <DataGate
        file="decision_quality.json"
        state={dq}
        emptyWhen={(d) => !d || d.enabled === false}
      >
        {(d) => {
          const a = d.attribution || {};
          const rows = Array.isArray(a.leaderboard) ? a.leaderboard : [];
          return (
            <>
              {rows.length > 0 ? (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Strategy</th>
                        <th>Episodes</th>
                        <th>Wins</th>
                        <th>Hit rate %</th>
                        <th>Avg fwd return %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r, i) => (
                        <tr key={i}>
                          <td className="mono small">{r.rank}</td>
                          <td>{r.strategy}</td>
                          <td className="mono small">{r.episodes}</td>
                          <td className="mono small">{r.wins}</td>
                          <td className="mono small">{r.hit_rate_pct}</td>
                          <td className={`mono small ${returnTone(r.avg_forward_return_pct)}`}>
                            {r.avg_forward_return_pct}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="muted small">No attribution data yet.</div>
              )}
              {a.note ? (
                <div className="muted small" style={{ marginTop: 8 }}>{a.note}</div>
              ) : null}
            </>
          );
        }}
      </DataGate>
    </Card>
  );
}
