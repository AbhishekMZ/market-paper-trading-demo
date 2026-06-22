import { useData } from '../hooks/useData.js';
import { Card, Stat, Money, Pct, DataGate } from './ui.jsx';
import { formatINR, formatInt, formatDate, formatPct } from '../lib/format.js';

function RiskStatusPill({ status }) {
  const s = String(status || '').toUpperCase();
  let tone = 'neutral';
  if (s === 'OK') tone = 'buy';
  else if (s.includes('TRIM') || s.includes('REVIEW') || s.includes('WATCH')) tone = 'hold';
  else if (s.includes('EXIT') || s.includes('STOP') || s.includes('SELL')) tone = 'danger';
  return <span className={`pill ${tone}`}>{status || '—'}</span>;
}

export default function Portfolio() {
  const portfolio = useData('portfolio.json');

  return (
    <DataGate file="portfolio.json" state={portfolio}>
      {(p) => {
        const positions = p.positions || [];
        const closed = p.closed || p.closed_positions || [];
        const closedIsArray = Array.isArray(closed);

        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Portfolio</h2>
              <p>
                Simulated holdings funded with fake money. As of {formatDate(p.as_of)} · starting
                capital {formatINR(p.starting_capital)}.
              </p>
            </div>

            <div className="grid cols-4">
              <Stat label="Total value" value={formatINR(p.total_value)} meta="cash + holdings" />
              <Stat label="Cash" value={formatINR(p.cash)} />
              <Stat label="Holdings value" value={formatINR(p.holdings_value)} />
              <Stat
                label="Max drawdown"
                value={formatPct(-Math.abs(Number(p.max_drawdown_pct || 0)))}
                tone={Number(p.max_drawdown_pct) ? 'neg' : 'zero'}
              />
            </div>

            <div className="grid cols-4">
              <Stat label="Realized P&L" value={<Money value={p.realized_pnl} signed />} />
              <Stat label="Unrealized P&L" value={<Money value={p.unrealized_pnl} signed />} />
              <Stat
                label="Total P&L"
                value={<Money value={p.total_pnl} signed />}
                meta={<Pct value={p.total_return_pct} />}
              />
              <Stat
                label="Budget this month"
                value={formatINR(p.capital_deployed)}
                meta={`of ${formatINR(p.monthly_capital)} · ${formatINR(
                  p.capital_remaining
                )} left`}
              />
            </div>

            <Card title="Open positions" sub={`${positions.length} held · all bot-managed, fake money`}>
              {positions.length === 0 ? (
                <div className="card-pad muted small">No open positions.</div>
              ) : (
                <div className="table-wrap">
                  <table className="data">
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th className="num-cell">Qty</th>
                        <th className="num-cell">Avg buy (₹)</th>
                        <th className="num-cell">Current (₹)</th>
                        <th className="num-cell">Unrealized P&L</th>
                        <th className="num-cell">P&L %</th>
                        <th>Risk status</th>
                        <th>Bot-owned</th>
                      </tr>
                    </thead>
                    <tbody>
                      {positions.map((pos, i) => (
                        <tr key={pos.symbol || i}>
                          <td className="sym">
                            {pos.symbol}
                            {pos.exchange ? <span className="exch">{pos.exchange}</span> : null}
                          </td>
                          <td className="num-cell">{formatInt(pos.quantity)}</td>
                          <td className="num-cell">{formatINR(pos.avg_price)}</td>
                          <td className="num-cell">{formatINR(pos.last_price)}</td>
                          <td className="num-cell">
                            <Money value={pos.unrealized_pnl} signed />
                          </td>
                          <td className="num-cell">
                            <Pct value={pos.unrealized_pnl_pct} />
                          </td>
                          <td>
                            <RiskStatusPill status={pos.risk_status} />
                          </td>
                          <td>
                            {pos.bot_owned ? (
                              <span className="pill watch">BOT</span>
                            ) : (
                              <span className="pill neutral">MANUAL</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>

            {closedIsArray && closed.length > 0 ? (
              <Card title="Closed positions" sub="Realized fake-money trades">
                <div className="table-wrap">
                  <table className="data">
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th className="num-cell">Qty</th>
                        <th className="num-cell">Avg buy (₹)</th>
                        <th className="num-cell">Exit (₹)</th>
                        <th className="num-cell">Realized P&L</th>
                        <th className="num-cell">P&L %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {closed.map((c, i) => (
                        <tr key={c.symbol || i}>
                          <td className="sym">{c.symbol}</td>
                          <td className="num-cell">{formatInt(c.quantity)}</td>
                          <td className="num-cell">{formatINR(c.avg_price)}</td>
                          <td className="num-cell">
                            {formatINR(c.exit_price ?? c.last_price ?? c.close_price)}
                          </td>
                          <td className="num-cell">
                            <Money value={c.realized_pnl ?? c.pnl} signed />
                          </td>
                          <td className="num-cell">
                            <Pct value={c.realized_pnl_pct ?? c.pnl_pct} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            ) : (
              <Card title="Closed positions">
                <div className="card-pad muted small">No closed positions yet.</div>
              </Card>
            )}
          </div>
        );
      }}
    </DataGate>
  );
}
