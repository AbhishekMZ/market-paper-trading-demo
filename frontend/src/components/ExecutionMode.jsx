import { Card, DataGate } from './ui.jsx';

function StatusLine({ label, value, good }) {
  // good === true  -> safe/expected state (green)
  // good === false -> the "disabled/blocked" safe state (also rendered calm)
  const tone = good ? 'ok' : 'neg';
  return (
    <div className="row between" style={{ padding: '11px 0', borderBottom: '1px solid var(--border-soft)' }}>
      <span className="muted">{label}</span>
      <span className={`pill ${tone === 'ok' ? 'buy' : 'danger'}`}>{value}</span>
    </div>
  );
}

export default function ExecutionMode({ report }) {
  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const e = data.execution || {};
        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Execution Mode</h2>
              <p>The hard guardrails that keep this demo from ever touching real money.</p>
            </div>

            <div className="callout danger">
              <strong>This is a fake-money demo.</strong> Real order placement is DISABLED at the
              config level. No broker is connected and no funds can be moved.
            </div>

            <div className="grid cols-2">
              <Card title="Current mode">
                <div className="card-pad" style={{ textAlign: 'center', padding: '34px 20px' }}>
                  <div className="pill watch" style={{ fontSize: 14, padding: '6px 16px' }}>
                    {String(e.mode || 'paper').toUpperCase()}
                  </div>
                  <div className="muted small" style={{ marginTop: 12 }}>
                    Broker adapter: <strong>{e.broker_adapter || 'paper'}</strong>
                  </div>
                </div>
              </Card>

              <Card title="Guardrail status">
                <div className="card-pad" style={{ paddingTop: 4, paddingBottom: 4 }}>
                  <StatusLine label="Live trading enabled" value={e.live_trading_enabled ? 'TRUE' : 'FALSE'} good={!e.live_trading_enabled} />
                  <StatusLine label="Angel One enabled" value={e.angel_one_enabled ? 'TRUE' : 'FALSE'} good={!e.angel_one_enabled} />
                  <StatusLine
                    label="Manual approval required"
                    value={e.require_manual_approval ? 'TRUE' : 'FALSE'}
                    good={!!e.require_manual_approval}
                  />
                  <StatusLine label="Allow real orders" value={e.allow_real_orders ? 'TRUE' : 'FALSE'} good={!e.allow_real_orders} />
                  <StatusLine label="Kill switch engaged" value={e.kill_switch ? 'TRUE' : 'FALSE'} good={!e.kill_switch} />
                </div>
              </Card>
            </div>

            <Card title="Plain-English summary">
              <div className="card-pad">
                <ul className="bullets">
                  <li>
                    <span className="ic">🟢</span>
                    <span>Current mode is <strong>PAPER</strong> — every order is simulated.</span>
                  </li>
                  <li>
                    <span className="ic">🔴</span>
                    <span>Live trading is <strong>false</strong>.</span>
                  </li>
                  <li>
                    <span className="ic">🔴</span>
                    <span>Angel One integration is <strong>false</strong> (disabled).</span>
                  </li>
                  <li>
                    <span className="ic">🟢</span>
                    <span>Manual approval is <strong>required</strong> before any real order could ever be considered.</span>
                  </li>
                  <li>
                    <span className="ic">🔴</span>
                    <span>Real order placement is <strong>DISABLED</strong>.</span>
                  </li>
                </ul>
              </div>
            </Card>
          </div>
        );
      }}
    </DataGate>
  );
}
