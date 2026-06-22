import { useData } from '../hooks/useData.js';
import { Card, Stat, Money, DataGate } from './ui.jsx';
import { formatInt, formatDate, humanizeKey, formatPct } from '../lib/format.js';

export default function StrategyEvaluation() {
  const evalData = useData('strategy_evaluation.json');

  return (
    <DataGate file="strategy_evaluation.json" state={evalData}>
      {(d) => {
        const strategies = d.strategies || {};
        const names = Object.keys(strategies);

        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Strategy Evaluation</h2>
              <p>
                Per-strategy performance over the paper-trading period. As of {formatDate(d.as_of)}.
                These are indicative diagnostics, not proof anything works.
              </p>
            </div>

            <div className="grid cols-4">
              <Stat label="Total signals" value={formatInt(d.total_signals)} />
              <Stat label="Paper trades" value={formatInt(d.total_paper_trades)} />
              <Stat
                label="Portfolio max drawdown"
                value={formatPct(-Math.abs(Number(d.portfolio_max_drawdown_pct || 0)))}
                tone={Number(d.portfolio_max_drawdown_pct) ? 'neg' : 'zero'}
              />
              <Stat label="Strategies tracked" value={formatInt(names.length)} />
            </div>

            {d.disclaimer ? (
              <div className="callout warn">
                <strong>Disclaimer: </strong>
                {d.disclaimer}
              </div>
            ) : null}

            <Card title="Per-strategy metrics">
              <div className="table-wrap">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Strategy</th>
                      <th className="num-cell">Signals</th>
                      <th className="num-cell">Paper trades</th>
                      <th className="num-cell">W / L</th>
                      <th className="num-cell">Win rate</th>
                      <th className="num-cell">Avg gain</th>
                      <th className="num-cell">Avg loss</th>
                      <th className="num-cell">False pos.</th>
                      <th className="num-cell">Avoided bad</th>
                      <th className="num-cell">Avg contrib.</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {names.map((name) => {
                      const m = strategies[name] || {};
                      return (
                        <tr key={name}>
                          <td className="sym">{humanizeKey(name)}</td>
                          <td className="num-cell">{formatInt(m.signals_generated)}</td>
                          <td className="num-cell">{formatInt(m.paper_trades_triggered)}</td>
                          <td className="num-cell">
                            {formatInt(m.wins)} / {formatInt(m.losses)}
                          </td>
                          <td className="num-cell">
                            {m.win_rate == null ? '—' : `${(Number(m.win_rate) * 100).toFixed(0)}%`}
                          </td>
                          <td className="num-cell">
                            <Money value={m.average_gain} signed />
                          </td>
                          <td className="num-cell">
                            <Money value={m.average_loss} signed />
                          </td>
                          <td className="num-cell">{formatInt(m.false_positive_count)}</td>
                          <td className="num-cell">{formatInt(m.avoided_bad_trade_count)}</td>
                          <td className="num-cell">
                            {m.average_score_contribution == null
                              ? '—'
                              : Number(m.average_score_contribution).toFixed(1)}
                          </td>
                          <td className="muted small" style={{ maxWidth: 240 }}>
                            {m.notes || '—'}
                          </td>
                        </tr>
                      );
                    })}
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
