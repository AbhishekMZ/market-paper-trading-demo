import { Card, DataGate } from './ui.jsx';
import { formatINR } from '../lib/format.js';

// Fixed, read-only policy values for the demo.
const FIXED = [
  ['Monthly cap', formatINR(10000)],
  ['Max per trade', formatINR(2000)],
  ['Max buys / day', '1'],
  ['Max buys / month', '5'],
  ['Mode', 'paper_trading_only'],
  ['Broker adapter', 'paper'],
  ['Notifications', 'email only'],
];

const BLOCKED_PRODUCTS = ['INTRADAY', 'MARGIN', 'F&O', 'OPTIONS', 'FUTURES'];
const BLOCKED_ORDER_TYPES = ['MARKET', 'SL'];
const LOSS_THRESHOLDS = [
  ['Soft review', '-7%'],
  ['Trim / reduce', '-10%'],
  ['Hard exit', '-15%'],
];

export default function SettingsView({ report }) {
  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const e = data.execution || {};
        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Settings</h2>
              <p>
                Read-only configuration. Nothing here is editable in the demo — these are the fixed
                safety limits the bot operates under.
              </p>
            </div>

            <div className="callout info">
              All settings below are <strong>read-only</strong>. They are baked into the bot’s
              config and surfaced here for transparency.
            </div>

            <div className="grid cols-2">
              <Card title="Capital & frequency limits">
                <div className="card-pad">
                  <dl className="kv">
                    {FIXED.map(([k, v]) => (
                      <div key={k} style={{ display: 'contents' }}>
                        <dt>{k}</dt>
                        <dd className="num">{v}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </Card>

              <Card title="Execution config (from report)">
                <div className="card-pad">
                  <dl className="kv">
                    <dt>Mode</dt>
                    <dd>{e.mode || 'paper'}</dd>
                    <dt>Broker adapter</dt>
                    <dd>{e.broker_adapter || 'paper'}</dd>
                    <dt>Live trading enabled</dt>
                    <dd>{String(!!e.live_trading_enabled)}</dd>
                    <dt>Angel One enabled</dt>
                    <dd>{String(!!e.angel_one_enabled)}</dd>
                    <dt>Require manual approval</dt>
                    <dd>{String(!!e.require_manual_approval)}</dd>
                    <dt>Allow real orders</dt>
                    <dd>{String(!!e.allow_real_orders)}</dd>
                    <dt>Kill switch</dt>
                    <dd>{String(!!e.kill_switch)}</dd>
                  </dl>
                </div>
              </Card>
            </div>

            <div className="grid cols-3">
              <Card title="Blocked products">
                <div className="card-pad row" style={{ gap: 8 }}>
                  {BLOCKED_PRODUCTS.map((p) => (
                    <span className="pill danger" key={p}>
                      {p}
                    </span>
                  ))}
                </div>
              </Card>
              <Card title="Blocked order types">
                <div className="card-pad row" style={{ gap: 8 }}>
                  {BLOCKED_ORDER_TYPES.map((p) => (
                    <span className="pill danger" key={p}>
                      {p}
                    </span>
                  ))}
                  <span className="dim small" style={{ width: '100%', marginTop: 6 }}>
                    Only delivery + limit orders are ever considered.
                  </span>
                </div>
              </Card>
              <Card title="Loss thresholds">
                <div className="card-pad">
                  <dl className="kv">
                    {LOSS_THRESHOLDS.map(([k, v]) => (
                      <div key={k} style={{ display: 'contents' }}>
                        <dt>{k}</dt>
                        <dd className="num neg">{v}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </Card>
            </div>
          </div>
        );
      }}
    </DataGate>
  );
}
