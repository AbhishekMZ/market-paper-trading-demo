// Decision Quality — the headline panel for the Decision Quality Engine.
// Answers "are the system's decisions actually good?" using measurement only;
// it never enables real trading.
import { useData } from '../hooks/useData.js';
import { Card, Stat, Pill, DataGate } from './ui.jsx';

// Return tinting: a number > 0 => 'pos', < 0 => 'neg', else ''.
function returnTone(value) {
  const n = Number(value);
  if (value === null || value === undefined || Number.isNaN(n) || n === 0) return '';
  return n > 0 ? 'pos' : 'neg';
}

function readinessTone(verdict) {
  if (verdict === 'EARLY_PROMISING') return 'ok';
  if (verdict === 'EARLY_WEAK') return 'warn';
  return 'neutral';
}

export default function DecisionQuality() {
  const dq = useData('decision_quality.json');

  return (
    <Card title="Decision Quality" sub="Are the system's decisions actually good? (measurement only)">
      <DataGate
        file="decision_quality.json"
        state={dq}
        emptyWhen={(d) => !d || d.enabled === false}
      >
        {(d) => {
          const m = d.metrics || {};
          const r = d.readiness || {};
          const benchOut = m.benchmark_outperformance_pct;
          return (
            <>
              <div className="stat-row">
                <Stat
                  label="Readiness"
                  value={<Pill tone={readinessTone(r.verdict)}>{r.verdict}</Pill>}
                />
                <Stat
                  label="Live trading"
                  value={<Pill tone="neg">{r.live_trading}</Pill>}
                />
              </div>
              <div className="stat-row">
                <Stat label="Tracked episodes" value={m.total_tracked_episodes ?? 0} />
                <Stat label="Matured" value={m.matured_episodes ?? 0} />
                <Stat label="Paper trades" value={m.paper_trades ?? 0} />
                <Stat label="Action rate %" value={m.action_rate_pct ?? 0} />
                <Stat
                  label="Acted fwd return %"
                  value={m.avg_forward_return_acted_pct ?? 0}
                  tone={returnTone(m.avg_forward_return_acted_pct)}
                />
                <Stat
                  label="Declined fwd return %"
                  value={m.avg_forward_return_not_acted_pct ?? 0}
                  tone={returnTone(m.avg_forward_return_not_acted_pct)}
                />
                <Stat
                  label="Decision edge %"
                  value={m.decision_edge_pct ?? 0}
                  tone={returnTone(m.decision_edge_pct)}
                />
                <Stat
                  label="Benchmark outperf %"
                  value={benchOut == null ? '—' : benchOut}
                  tone={benchOut == null ? '' : returnTone(benchOut)}
                />
              </div>
              {Array.isArray(r.reasons) && r.reasons.length > 0 ? (
                <ul className="muted small" style={{ marginTop: 8 }}>
                  {r.reasons.map((reason, i) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              ) : null}
              {d.disclaimer ? (
                <div className="muted small" style={{ marginTop: 8, fontStyle: 'italic' }}>
                  {d.disclaimer}
                </div>
              ) : null}
            </>
          );
        }}
      </DataGate>
    </Card>
  );
}
