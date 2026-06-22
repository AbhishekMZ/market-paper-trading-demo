import { Card, DataGate } from './ui.jsx';

export default function FutureReadiness({ report }) {
  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const items = Array.isArray(data.future_readiness) ? data.future_readiness : [];
        const done = items.filter((i) => i.done).length;

        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Future Readiness</h2>
              <p>
                A checklist of what would need to be true before this system could ever graduate
                beyond paper trading. {done} of {items.length} complete.
              </p>
            </div>

            <Card title="Readiness checklist">
              <div className="card-pad">
                {items.length === 0 ? (
                  <div className="muted small">No readiness items reported.</div>
                ) : (
                  <ul className="checklist">
                    {items.map((it, i) => (
                      <li key={i} className={it.done ? 'done' : 'pending'}>
                        <span className="box">{it.done ? '✅' : '⬜'}</span>
                        <span>{it.item}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </Card>

            <div className="callout info">
              <strong>Phases 2–4 are future work and currently disabled.</strong> The roadmap moves
              deliberately: <strong>Phase 2</strong> adds manual-approval real trading,{' '}
              <strong>Phase 3</strong> allows limited real execution (delivery + limit orders only),
              and <strong>Phase 4</strong> introduces controlled automation with a kill switch. None
              of these are active — this demo never leaves Phase 1 (paper trading).
            </div>
          </div>
        );
      }}
    </DataGate>
  );
}
