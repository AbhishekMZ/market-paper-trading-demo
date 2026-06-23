// Shadow & blocked decisions — did acting vs declining add value? Compares the
// forward returns of acted picks, declined shadow candidates, and blocked names.
import { useData } from '../hooks/useData.js';
import { Card, Stat, Pill, DataGate } from './ui.jsx';

// Return tinting: a number > 0 => 'pos', < 0 => 'neg', else ''.
function returnTone(value) {
  const n = Number(value);
  if (value === null || value === undefined || Number.isNaN(n) || n === 0) return '';
  return n > 0 ? 'pos' : 'neg';
}

function newsTone(level) {
  if (level === 'CRITICAL' || level === 'HIGH') return 'neg';
  if (level === 'MEDIUM') return 'warn';
  return 'neutral';
}

export default function ShadowSignals() {
  const dq = useData('decision_quality.json');

  return (
    <Card title="Shadow & blocked decisions" sub="Did acting vs declining add value?">
      <DataGate
        file="decision_quality.json"
        state={dq}
        emptyWhen={(d) => !d || d.enabled === false}
      >
        {(d) => {
          const s = d.shadow || {};
          const acted = s.acted || {};
          const candidates = s.shadow_candidates || {};
          const blocked = s.blocked || {};
          const examples = Array.isArray(s.shadow_examples) ? s.shadow_examples : [];
          return (
            <>
              <div className="stat-row">
                <Stat
                  label="Acted avg %"
                  value={acted.avg_return_pct ?? 0}
                  tone={returnTone(acted.avg_return_pct)}
                />
                <Stat
                  label="Shadow candidates avg %"
                  value={candidates.avg_return_pct ?? 0}
                  tone={returnTone(candidates.avg_return_pct)}
                />
                <Stat
                  label="Blocked avg %"
                  value={blocked.avg_return_pct ?? 0}
                  tone={returnTone(blocked.avg_return_pct)}
                />
                <Stat
                  label="Acted-vs-shadow edge %"
                  value={s.acted_vs_shadow_edge_pct ?? 0}
                  tone={returnTone(s.acted_vs_shadow_edge_pct)}
                />
              </div>
              {s.decision_note ? (
                <div className="muted small" style={{ marginTop: 8 }}>{s.decision_note}</div>
              ) : null}
              {s.block_note ? (
                <div className="muted small">{s.block_note}</div>
              ) : null}
              {examples.length > 0 ? (
                <div className="table-wrap" style={{ marginTop: 8 }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Score</th>
                        <th>Label</th>
                        <th>News</th>
                        <th>Fwd return %</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {examples.map((e, i) => (
                        <tr key={i}>
                          <td>{e.symbol}</td>
                          <td className="mono small">{e.score}</td>
                          <td className="small">{e.label_at_open}</td>
                          <td><Pill tone={newsTone(e.news_risk_level)}>{e.news_risk_level}</Pill></td>
                          <td className={`mono small ${returnTone(e.forward_return_pct)}`}>
                            {e.forward_return_pct}
                          </td>
                          <td className="small dim">{e.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="muted small" style={{ marginTop: 8 }}>
                  No shadow examples yet.
                </div>
              )}
            </>
          );
        }}
      </DataGate>
    </Card>
  );
}
