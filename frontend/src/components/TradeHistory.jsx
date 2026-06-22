import { useData } from '../hooks/useData.js';
import { Card, Money, DataGate } from './ui.jsx';
import { formatINR, formatInt, formatDateTime } from '../lib/format.js';

function SidePill({ side }) {
  const s = String(side || '').toUpperCase();
  if (s === 'BUY') return <span className="pill buy">BUY</span>;
  if (s === 'SELL') return <span className="pill danger">SELL</span>;
  return <span className="pill neutral">{side || '—'}</span>;
}

function StatusPill({ status }) {
  const s = String(status || '').toUpperCase();
  let tone = 'neutral';
  if (s === 'FILLED') tone = 'buy';
  else if (s === 'REJECTED' || s === 'CANCELLED' || s === 'FAILED') tone = 'danger';
  else if (s === 'PENDING' || s === 'OPEN') tone = 'hold';
  return <span className={`pill ${tone}`}>{status || '—'}</span>;
}

export default function TradeHistory() {
  const trades = useData('trade_history.json');

  return (
    <DataGate
      file="trade_history.json"
      state={trades}
      emptyWhen={(d) => Array.isArray(d) && d.length === 0}
    >
      {(data) => {
        const rows = Array.isArray(data) ? data : [];
        return (
          <div className="stack">
            <div className="view-head">
              <h2>Trade History</h2>
              <p>
                Every simulated order placed by the bot. <span className="tag paper">PAPER</span>{' '}
                — no real money, no real broker, no real fills.
              </p>
            </div>

            <Card>
              <div className="table-wrap">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Date / time</th>
                      <th>Action</th>
                      <th>Symbol</th>
                      <th className="num-cell">Qty</th>
                      <th className="num-cell">Price (₹)</th>
                      <th className="num-cell">Amount (₹)</th>
                      <th>Status</th>
                      <th className="num-cell">Realized P&L</th>
                      <th>Broker</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((t, i) => (
                      <tr key={t.order_id || i}>
                        <td className="muted small" style={{ whiteSpace: 'nowrap' }}>
                          {formatDateTime(t.timestamp)}
                        </td>
                        <td>
                          <SidePill side={t.side} />
                        </td>
                        <td className="sym">{t.symbol}</td>
                        <td className="num-cell">
                          {formatInt(t.filled_quantity ?? t.quantity)}
                        </td>
                        <td className="num-cell">{formatINR(t.price)}</td>
                        <td className="num-cell">{formatINR(t.amount)}</td>
                        <td>
                          <StatusPill status={t.status} />
                        </td>
                        <td className="num-cell">
                          <Money value={t.realized_pnl} signed />
                        </td>
                        <td>
                          <span className="tag paper">{t.broker_adapter || 'paper'}</span>
                        </td>
                        <td className="muted small" style={{ maxWidth: 280 }}>
                          {t.reason || t.message || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        );
      }}
    </DataGate>
  );
}
