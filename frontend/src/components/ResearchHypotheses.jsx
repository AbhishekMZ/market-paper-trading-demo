import { Card, Stat, DataGate } from './ui.jsx';
import { formatInt, humanizeKey } from '../lib/format.js';

export default function ResearchHypotheses({ report }) {
  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const r = data.research || {};
        const byStatus = r.by_status || {};
        const testing = r.testing || [];
        const eligible = r.real_trading_eligible || [];

        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Research Hypotheses</h2>
              <p>
                Experimental strategy ideas under evaluation. These are{' '}
                <strong>hypotheses, not trusted rules</strong>.
              </p>
            </div>

            <div className="callout info">
              Research strategies are <strong>guesses about what might work</strong>. They must
              survive a full paper-validation period — net of costs, across enough trades — before
              any of them is allowed to influence a real order. None are trusted by default.
            </div>

            <div className="grid cols-3">
              <Stat label="Total hypotheses" value={formatInt(r.total)} />
              <Stat label="In paper testing" value={formatInt(testing.length)} />
              <Stat
                label="Real-trading eligible"
                value={formatInt(eligible.length)}
                tone={eligible.length ? 'pos' : 'zero'}
                meta={eligible.length ? 'passed validation' : 'none yet — as intended'}
              />
            </div>

            <div className="grid cols-2">
              <Card title="By status">
                {Object.keys(byStatus).length === 0 ? (
                  <div className="card-pad muted small">No status breakdown available.</div>
                ) : (
                  <div className="card-pad">
                    <dl className="kv">
                      {Object.entries(byStatus).map(([k, v]) => (
                        <div key={k} style={{ display: 'contents' }}>
                          <dt>{humanizeKey(k)}</dt>
                          <dd className="num">{formatInt(v)}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                )}
              </Card>

              <Card title="Currently testing" sub="Hypotheses collecting paper evidence">
                <div className="card-pad">
                  {testing.length === 0 ? (
                    <div className="muted small">Nothing in testing.</div>
                  ) : (
                    <div className="row" style={{ gap: 8 }}>
                      {testing.map((id) => (
                        <span className="pill watch" key={id}>
                          {id}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="divider" />
                  <div className="label dim small" style={{ marginBottom: 8 }}>
                    Real-trading eligible
                  </div>
                  {eligible.length === 0 ? (
                    <div className="muted small">
                      None. No hypothesis has earned real-money trust — and in this demo none ever
                      will, because real trading is disabled.
                    </div>
                  ) : (
                    <div className="row" style={{ gap: 8 }}>
                      {eligible.map((id) => (
                        <span className="pill buy" key={id}>
                          {id}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </div>
        );
      }}
    </DataGate>
  );
}
