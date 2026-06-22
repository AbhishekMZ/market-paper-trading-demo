import { Card } from './ui.jsx';

const STATIC_CAUTIONS = [
  {
    t: 'Avoid overfitting',
    d: 'A strategy tuned to fit past prices perfectly usually fails on new data. Prefer simple, robust rules.',
  },
  {
    t: 'Beware look-ahead bias',
    d: 'Never let a signal use information that would not have been available at decision time.',
  },
  {
    t: 'Account for survivorship bias',
    d: 'Backtests that ignore delisted/failed companies overstate returns. The surviving names look better than reality.',
  },
  {
    t: 'Include costs & slippage',
    d: 'Brokerage, STT, exchange fees, stamp duty and slippage quietly erode edge. Always evaluate net of costs.',
  },
  {
    t: 'One month proves nothing',
    d: 'A handful of paper trades is not a statistically meaningful sample. Do not trust short-run win rates.',
  },
  {
    t: 'Prefer fewer high-quality trades',
    d: 'Trading less, but only on high-conviction setups, beats churning through marginal signals.',
  },
];

/**
 * Static-but-important bias panel + dynamic data_quality_warnings and conflicts
 * surfaced from latest_report.
 */
export default function BiasWarnings({ dataQualityWarnings = [], conflicts = [] }) {
  return (
    <Card
      title="Bias & Data-Quality Cautions"
      sub="Why we treat results with humility"
    >
      <div className="card-pad stack" style={{ gap: 14 }}>
        <ul className="bullets">
          {STATIC_CAUTIONS.map((c) => (
            <li key={c.t}>
              <span className="ic">⚠️</span>
              <span>
                <strong>{c.t}.</strong> <span className="muted">{c.d}</span>
              </span>
            </li>
          ))}
        </ul>

        <div className="divider" />

        <div>
          <div className="label dim small" style={{ marginBottom: 6 }}>
            Data-quality warnings (this run)
          </div>
          {dataQualityWarnings.length === 0 ? (
            <p className="muted small" style={{ margin: 0 }}>
              No data-quality warnings reported.
            </p>
          ) : (
            <ul className="clean small">
              {dataQualityWarnings.map((w, i) => (
                <li key={i} className="muted">
                  {w}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <div className="label dim small" style={{ marginBottom: 6 }}>
            Strategy conflicts (this run)
          </div>
          {conflicts.length === 0 ? (
            <p className="muted small" style={{ margin: 0 }}>
              No strategy conflicts reported.
            </p>
          ) : (
            <ul className="clean small">
              {conflicts.map((c, i) => (
                <li key={i} className="muted">
                  {c}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Card>
  );
}
