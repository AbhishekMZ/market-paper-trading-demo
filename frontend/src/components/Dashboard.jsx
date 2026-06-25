import { useData } from '../hooks/useData.js';
import { Card, Stat, Money, Pct, DataGate, LabelPill, RiskPill } from './ui.jsx';
import {
  formatINR,
  formatInt,
  formatDateTime,
  formatScore,
  formatConfidence,
} from '../lib/format.js';
import MarketRegimeCard from './MarketRegimeCard.jsx';
import BiasWarnings from './BiasWarnings.jsx';
import EvidenceSummary from './EvidenceSummary.jsx';

function pct(part, whole) {
  const p = Number(part);
  const w = Number(whole);
  if (!w || Number.isNaN(p) || Number.isNaN(w)) return null;
  return (p / w) * 100;
}

export default function Dashboard({ report }) {
  const apiUsage = useData('api_usage.json');

  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const p = data.portfolio || {};
        const cap = data.cost_adjusted_pnl || {};
        const candidates =
          (data.top_candidates && data.top_candidates.length
            ? data.top_candidates
            : data.signals) || [];
        const openPositions = (p.positions || []).length;
        const budgetUsedPct = pct(p.capital_deployed, p.monthly_capital);
        const callsToday =
          apiUsage.data?.calls_today ?? data.api_usage?.calls_today ?? null;

        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Dashboard</h2>
              <p>
                A snapshot of the fake-money portfolio, today’s signals and the market backdrop.
                Generated {formatDateTime(data.generated_at)} ({data.checkpoint} checkpoint).
              </p>
            </div>

            {data.decision_quality ? (
              <EvidenceSummary
                summary={data.decision_quality.evidence_summary}
                metrics={data.decision_quality.metrics}
                readiness={data.decision_quality.readiness}
              />
            ) : null}

            {/* Top metric tiles */}
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
                meta={`${formatInt(p.buys_this_month)} / ${formatInt(
                  p.max_buys_per_month ?? p.max_buys_per_month
                )} buys this month`}
              />
              <Stat
                label="Market-data calls today"
                value={callsToday == null ? '—' : formatInt(callsToday)}
                meta={apiUsage.data?.provider ? `via ${apiUsage.data.provider}` : 'data provider'}
              />
            </div>

            {/* Budget + execution row */}
            <div className="grid cols-4">
              <Stat
                label="Monthly budget used"
                value={formatINR(p.capital_deployed)}
                meta={
                  budgetUsedPct == null
                    ? `of ${formatINR(p.monthly_capital)}`
                    : `${budgetUsedPct.toFixed(1)}% of ${formatINR(p.monthly_capital)}`
                }
              />
              <Stat
                label="Capital remaining"
                value={formatINR(p.capital_remaining)}
                meta="available this month"
              />
              <Stat label="Execution mode" value="PAPER ONLY" tone="zero" meta="no real orders" />
              <Stat label="Live trading" value="DISABLED" tone="neg" meta="Angel One disabled" />
            </div>

            {/* Cost-adjusted P&L */}
            <Card
              title="Cost-adjusted P&L"
              sub="Net of estimated Indian delivery costs (brokerage, STT, fees, stamp duty)"
            >
              <div className="card-pad">
                <div className="grid cols-4">
                  <Stat label="Gross realized P&L" value={<Money value={cap.gross_realized_pnl} signed />} />
                  <Stat label="Estimated costs" value={<Money value={cap.estimated_costs} />} />
                  <Stat
                    label="Net realized (cost-adj.)"
                    value={<Money value={cap.net_realized_pnl_cost_adjusted} signed />}
                  />
                  <Stat
                    label="Win rate"
                    value={
                      cap.win_rate_pct == null ? '—' : `${Number(cap.win_rate_pct).toFixed(1)}%`
                    }
                    meta={`${formatInt(cap.closed_trades)} closed · ${formatInt(
                      cap.wins
                    )}W / ${formatInt(cap.losses)}L`}
                  />
                </div>
                <div className="row" style={{ marginTop: 12, gap: 18 }}>
                  <span className="small muted">
                    Best trade: <Money value={cap.best_trade} signed />
                  </span>
                  <span className="small muted">
                    Worst trade: <Money value={cap.worst_trade} signed />
                  </span>
                  <span className="tag paper">cost-adjusted (estimated Indian delivery costs)</span>
                </div>
              </div>
            </Card>

            {/* Regime + bias side by side */}
            <div className="grid cols-2">
              <MarketRegimeCard regime={data.market_regime} />
              <BiasWarnings
                dataQualityWarnings={data.data_quality_warnings || []}
                conflicts={data.conflicts || []}
              />
            </div>

            {/* Today's top signals */}
            <Card title="Today’s top signals" sub="Highest-scoring candidates from this run">
              {candidates.length === 0 ? (
                <div className="card-pad muted small">No candidate signals in this run.</div>
              ) : (
                <div className="table-wrap">
                  <table className="data">
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Name</th>
                        <th className="num-cell">Score</th>
                        <th>Signal</th>
                        <th className="num-cell">Conf.</th>
                        <th>Risk</th>
                        <th className="num-cell">Last price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {candidates.slice(0, 6).map((s) => (
                        <tr key={s.signal_id || s.symbol}>
                          <td className="sym">
                            {s.symbol}
                            {s.exchange ? <span className="exch">{s.exchange}</span> : null}
                          </td>
                          <td className="muted">{s.name || '—'}</td>
                          <td className="num-cell">{formatScore(s.score)}</td>
                          <td>
                            <LabelPill label={s.label} />
                          </td>
                          <td className="num-cell">{formatConfidence(s.confidence)}</td>
                          <td>
                            <RiskPill risk={s.risk_level} />
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
