import { Card, RegimePill } from './ui.jsx';
import { regimeMeta, formatScore, formatConfidence, humanizeKey } from '../lib/format.js';

/**
 * Shows latest_report.market_regime: {regime, score, confidence, reason, inputs,
 * blocks_new_buys, timestamp}. Color by regime; explains what it means for buys.
 */
export default function MarketRegimeCard({ regime }) {
  if (!regime) {
    return (
      <Card title="Market Regime">
        <div className="card-pad muted small">No market-regime data available.</div>
      </Card>
    );
  }

  const meta = regimeMeta(regime.regime);
  const blocks = regime.blocks_new_buys;
  const inputs = regime.inputs || {};
  const benchmarks = inputs.benchmarks || {};

  return (
    <Card
      title="Market Regime"
      sub="Top-down read of the market before any stock is scored"
      headRight={<RegimePill regime={regime.regime} />}
    >
      <div className="card-pad stack" style={{ gap: 14 }}>
        <div className="row" style={{ gap: 22 }}>
          <div>
            <div className="label dim small">Score</div>
            <div className="value num" style={{ fontSize: 22 }}>
              {formatScore(regime.score)}
              <span className="dim" style={{ fontSize: 13 }}>
                {' '}
                / 100
              </span>
            </div>
          </div>
          <div>
            <div className="label dim small">Confidence</div>
            <div className="value num" style={{ fontSize: 22 }}>
              {formatConfidence(regime.confidence)}
            </div>
          </div>
          <div>
            <div className="label dim small">New buys</div>
            <div className="value" style={{ fontSize: 16, marginTop: 6 }}>
              {blocks ? (
                <span className="pill danger">BLOCKED</span>
              ) : (
                <span className="pill buy">ALLOWED</span>
              )}
            </div>
          </div>
        </div>

        {regime.reason ? <p className="muted small" style={{ margin: 0 }}>{regime.reason}</p> : null}

        <div className={`callout ${blocks ? 'danger' : 'ok'}`}>
          <strong>What this means: </strong>
          {meta.blurb}
          {blocks
            ? ' Right now the regime is actively blocking new paper buys.'
            : ' New paper buys are currently permitted, subject to per-signal risk checks.'}
        </div>

        {Object.keys(benchmarks).length > 0 || Object.keys(inputs).length > 0 ? (
          <div>
            <div className="label dim small" style={{ marginBottom: 6 }}>
              Inputs
            </div>
            <dl className="kv">
              {Object.entries(benchmarks).map(([k, v]) => (
                <RegimeKV key={k} k={k} v={`${Number(v) > 0 ? '+' : ''}${v}%`} />
              ))}
              {inputs.avg_change_pct != null ? (
                <RegimeKV k="Avg change" v={`${inputs.avg_change_pct}%`} />
              ) : null}
              {inputs.index_volatility_pct != null ? (
                <RegimeKV k="Index volatility" v={`${inputs.index_volatility_pct}%`} />
              ) : null}
              {inputs.max_abs_move_pct != null ? (
                <RegimeKV k="Max abs move" v={`${inputs.max_abs_move_pct}%`} />
              ) : null}
            </dl>
          </div>
        ) : null}
      </div>
    </Card>
  );
}

function RegimeKV({ k, v }) {
  return (
    <>
      <dt>{humanizeKey(k)}</dt>
      <dd className="num">{v}</dd>
    </>
  );
}
