// Escalation Queue — what the observer escalated for review or paper action,
// and the decision that came out of it (newest first).
import { useData } from '../hooks/useData.js';
import { Card, Pill, DataGate } from './ui.jsx';
import { formatDateTime } from '../lib/format.js';

function severityTone(s) {
  if (s === 'CRITICAL' || s === 'HIGH') return 'neg';
  if (s === 'MEDIUM') return 'warn';
  if (s === 'LOW') return 'info';
  return 'neutral';
}

function actionTone(a) {
  const t = String(a || '');
  if (t.startsWith('BLOCKED') || t === 'SELL_REVIEW' || t === 'EXIT_REVIEW' || t === 'TRIM_REVIEW') return 'warn';
  if (t === 'PAPER_BUY_ALLOWED') return 'ok';
  if (t === 'MANUAL_REVIEW') return 'warn';
  return 'neutral';
}

export default function EscalationQueue() {
  const queue = useData('escalation_queue.json');

  return (
    <Card title="Escalation queue" sub="What the observer escalated, and the decision">
      <DataGate
        file="escalation_queue.json"
        state={queue}
        emptyWhen={(d) => !Array.isArray(d) || d.length === 0}
      >
        {(rows) => (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Severity</th>
                  <th>Action</th>
                  <th>Manual review</th>
                  <th>Focused</th>
                  <th>Final decision</th>
                  <th>Email</th>
                  <th>Expires</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => {
                  const fa = r.focused_analysis_result;
                  return (
                    <tr key={i}>
                      <td>{r.symbol}</td>
                      <td><Pill tone={severityTone(r.severity)}>{r.severity || '—'}</Pill></td>
                      <td><Pill tone={actionTone(r.action_type)}>{r.action_type || '—'}</Pill></td>
                      <td>{r.manual_review_required ? <Pill tone="warn">yes</Pill> : <span className="dim">no</span>}</td>
                      <td>{fa ? `${fa.label} ${fa.score}` : '—'}</td>
                      <td>{r.final_decision}</td>
                      <td className="small">{r.email_sent ? 'sent' : '—'}</td>
                      <td className="mono small">{formatDateTime(r.expires_at)}</td>
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
