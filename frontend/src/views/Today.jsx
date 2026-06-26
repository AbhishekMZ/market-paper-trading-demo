// "Today" view: the at-a-glance landing. Snapshot tiles, a one-line run headline,
// and the full list of calls. Clicking a call row jumps to Why for that stock.
import { useData } from '../hooks/useData.js';
import { DataGate, Card, Stat, Money, Pct, LabelPill, RiskPill } from '../components/ui.jsx';
import { formatINR, formatInt, formatScore, formatDateTime } from '../lib/format.js';
import { runHeadline } from '../lib/narrative.js';

function pct(part, whole) {
  const p = Number(part);
  const w = Number(whole);
  if (!w || Number.isNaN(p) || Number.isNaN(w)) return null;
  return (p / w) * 100;
}

export default function Today({ report, onSelectSymbol }) {
  const apiUsage = useData('api_usage.json');

  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const p = data.portfolio || {};
        const calls = (data.signals || [])
          .slice()
          .sort((a, b) => Number(b.score) - Number(a.score));
        const openPositions = (p.positions || []).length;
        const budgetUsedPct = pct(p.capital_deployed, p.monthly_capital);

        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Today</h2>
              <p>
                Generated {formatDateTime(data.generated_at)} ({data.checkpoint} checkpoint).
              </p>
            </div>

            <div className="callout info">
              <strong>{runHeadline(data)}</strong>
            </div>

            <div className="grid cols-4">
              <Stat
                label="Fake capital (total value)"
                value={formatINR(p.total_value)}
                meta={`Starting ${formatINR(p.starting_capital)}`}
              />
              <Stat
                label="Total P&L"
                value={<Money value={p.total_pnl} signed />}
                meta={<Pct value={p.total_return_pct} />}
              />
              <Stat
                label="Open positions"
                value={formatInt(openPositions)}
                meta={`${formatInt(p.buys_this_month)} / ${formatInt(p.max_buys_per_month)} buys this month`}
              />
              <Stat
                label="Capital remaining"
                value={formatINR(p.capital_remaining)}
                meta={
                  budgetUsedPct == null
                    ? `of ${formatINR(p.monthly_capital)}`
                    : `${budgetUsedPct.toFixed(1)}% used of ${formatINR(p.monthly_capital)}`
                }
              />
            </div>

            <Card title="Today’s calls" sub="Every stock scored this run — click a row to see why">
              {calls.length === 0 ? (
                <div className="card-pad muted small">No candidate signals in this run.</div>
              ) : (
                <div className="table-wrap">
                  <table className="data">
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Name</th>
                        <th className="num-cell">Score</th>
                        <th>Call</th>
                        <th>Risk</th>
                        <th>Why (short)</th>
                        <th className="num-cell">Last price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {calls.map((s) => (
                        <tr
                          key={s.signal_id || s.symbol}
                          className="clickable"
                          onClick={() => onSelectSymbol && onSelectSymbol(s.symbol)}
                        >
                          <td className="sym">
                            {s.symbol}
                            {s.exchange ? <span className="exch">{s.exchange}</span> : null}
                          </td>
                          <td className="muted">{s.name || '—'}</td>
                          <td className="num-cell">{formatScore(s.score)}</td>
                          <td>
                            <LabelPill label={s.label} />
                          </td>
                          <td>
                            <RiskPill risk={s.risk_level} />
                          </td>
                          <td className="muted small" style={{ maxWidth: 360 }}>
                            {s.reason || '—'}
                          </td>
                          <td className="num-cell">{formatINR(s.last_price)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        );
      }}
    </DataGate>
  );
}
