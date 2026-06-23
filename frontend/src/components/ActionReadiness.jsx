// Swift Action Readiness — explains why action was or was not taken this run.
// "Swift action" means a paper action or a manual-review alert, never a real
// order. Every paper buy still passes Risk + News + Data-Quality + limits.
import { useData } from '../hooks/useData.js';
import { Card, Stat, Pill, DataGate } from './ui.jsx';

export default function ActionReadiness() {
  const report = useData('observation_report.json');

  return (
    <Card title="Swift action readiness" sub="Why action was or was not taken (paper-only)">
      <DataGate file="observation_report.json" state={report}>
        {(r) => {
          const taken = r.actions_taken?.length ?? 0;
          const blocked = r.blocked_actions?.length ?? 0;
          return (
            <>
              <div className="stat-row">
                <Stat label="Paper action" value={<Pill tone="info">ENABLED (paper)</Pill>} />
                <Stat label="Real orders" value={<Pill tone="neg">DISABLED</Pill>} />
                <Stat label="Auto-sell" value={<Pill tone="neg">DISABLED (review-only)</Pill>} />
              </div>
              <div className="stat-row">
                <Stat label="Actions taken" value={taken} tone={taken > 0 ? 'pos' : ''} />
                <Stat label="Blocked" value={blocked} tone={blocked > 0 ? 'neg' : ''} />
                <Stat label="Emails sent" value={r.emails_sent ?? 0} />
              </div>
              {Array.isArray(r.blocked_actions) && r.blocked_actions.length > 0 ? (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Blocked by</th>
                        <th>Trigger</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.blocked_actions.map((b, i) => (
                        <tr key={i}>
                          <td>{b.symbol}</td>
                          <td><Pill tone="warn">{b.blocked_by}</Pill></td>
                          <td>{b.trigger}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="muted small" style={{ marginTop: 8 }}>No actions blocked this run.</div>
              )}
              <div className="muted small" style={{ marginTop: 8 }}>
                Swift action means a swift PAPER action or a manual-review alert — never a real
                order. Every paper buy still passes Risk + News + Data-Quality + limits via
                ExecutionEngine.
              </div>
            </>
          );
        }}
      </DataGate>
    </Card>
  );
}
