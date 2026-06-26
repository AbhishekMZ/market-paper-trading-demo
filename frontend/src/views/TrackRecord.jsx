// "Track Record" view: is the engine actually making good calls? Reuses the
// existing EvidenceSummary (maturity + decision edge) and BenchmarkComparison
// (vs the index), plus cost-adjusted realised P&L from the report.
import { useData } from '../hooks/useData.js';
import { DataGate, Card, Stat, Money } from '../components/ui.jsx';
import { formatInt } from '../lib/format.js';
import EvidenceSummary from '../components/EvidenceSummary.jsx';
import BenchmarkComparison from '../components/BenchmarkComparison.jsx';

export default function TrackRecord({ report }) {
  const dq = useData('decision_quality.json');

  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const cap = data.cost_adjusted_pnl || {};
        const dqData = dq.data && dq.data.enabled !== false ? dq.data : null;
        const evidence = dqData || data.decision_quality || null;

        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Track Record</h2>
              <p>
                Is the engine actually making good calls? Maturity, edge versus the index, and
                realised paper P&L — net of estimated Indian delivery costs.
              </p>
            </div>

            {evidence ? (
              <EvidenceSummary
                summary={evidence.evidence_summary}
                metrics={evidence.metrics}
                readiness={evidence.readiness}
              />
            ) : null}

            <Card
              title="Cost-adjusted realised P&L"
              sub="Net of estimated Indian delivery costs (brokerage, STT, fees, stamp duty)"
            >
              <div className="card-pad">
                <div className="grid cols-4">
                  <Stat label="Gross realised P&L" value={<Money value={cap.gross_realized_pnl} signed />} />
                  <Stat label="Estimated costs" value={<Money value={cap.estimated_costs} />} />
                  <Stat
                    label="Net realised (cost-adj.)"
                    value={<Money value={cap.net_realized_pnl_cost_adjusted} signed />}
                  />
                  <Stat
                    label="Win rate"
                    value={cap.win_rate_pct == null ? '—' : `${Number(cap.win_rate_pct).toFixed(1)}%`}
                    meta={`${formatInt(cap.closed_trades)} closed · ${formatInt(cap.wins)}W / ${formatInt(cap.losses)}L`}
                  />
                </div>
              </div>
            </Card>

            <BenchmarkComparison />
          </div>
        );
      }}
    </DataGate>
  );
}
