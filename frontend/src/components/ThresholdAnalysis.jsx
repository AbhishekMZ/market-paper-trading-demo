// Threshold analysis — descriptive only. Shows which score threshold would have
// worked best on the data so far. The live buy threshold is fixed in config and
// is NEVER auto-tuned in v1.
import { useData } from '../hooks/useData.js';
import { Card, Stat, Pill, DataGate } from './ui.jsx';

// Return tinting: a number > 0 => 'pos', < 0 => 'neg', else ''.
function returnTone(value) {
  const n = Number(value);
  if (value === null || value === undefined || Number.isNaN(n) || n === 0) return '';
  return n > 0 ? 'pos' : 'neg';
}

export default function ThresholdAnalysis() {
  const dq = useData('decision_quality.json');

  return (
    <Card
      title="Threshold analysis"
      sub="What score threshold would have worked best? (descriptive — never auto-tuned)"
    >
      <DataGate
        file="decision_quality.json"
        state={dq}
        emptyWhen={(d) => !d || d.enabled === false}
      >
        {(d) => {
          const t = d.threshold_analysis || {};
          const rows = Array.isArray(t.table) ? t.table : [];
          return (
            <>
              <div className="stat-row">
                <Stat
                  label="Tuning"
                  value={<Pill tone="neutral">{`Auto-tuning: ${t.auto_tuning}`}</Pill>}
                />
                <Stat label="Best observed" value={t.best_threshold_observed ?? '—'} />
              </div>
              {rows.length > 0 ? (
                <div className="table-wrap" style={{ marginTop: 8 }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Threshold</th>
                        <th>Would-buy count</th>
                        <th>Hit rate %</th>
                        <th>Avg fwd return %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r, i) => (
                        <tr key={i}>
                          <td className="mono small">{r.threshold}</td>
                          <td className="mono small">{r.would_buy_count}</td>
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
                <div className="muted small" style={{ marginTop: 8 }}>
                  No threshold data yet.
                </div>
              )}
              {t.note ? (
                <div className="muted small" style={{ marginTop: 8 }}>{t.note}</div>
              ) : null}
            </>
          );
        }}
      </DataGate>
    </Card>
  );
}
