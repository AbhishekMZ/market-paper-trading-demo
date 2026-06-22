import { useState } from 'react';
import { DataGate, LabelPill, RiskPill, Card } from './ui.jsx';
import {
  formatScore,
  formatConfidence,
  formatDateTime,
  formatINR,
} from '../lib/format.js';
import StrategyBreakdown from './StrategyBreakdown.jsx';

export default function SignalTable({ report }) {
  const [open, setOpen] = useState(null);

  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const signals = data.signals || [];
        return (
          <div className="stack">
            <div className="view-head">
              <h2>Signals</h2>
              <p>
                Every stock scored in this run. Click a row to expand the full strategy breakdown,
                final recommendation, cost estimate and the data snapshot used.
              </p>
            </div>

            <Card>
              {signals.length === 0 ? (
                <div className="card-pad muted small">No signals in this run.</div>
              ) : (
                <div className="table-wrap">
                  <table className="data">
                    <thead>
                      <tr>
                        <th style={{ width: 16 }} />
                        <th>Symbol</th>
                        <th>Name</th>
                        <th className="num-cell">Score</th>
                        <th>Signal</th>
                        <th className="num-cell">Conf.</th>
                        <th>Risk</th>
                        <th>Reason</th>
                        <th>Last checked</th>
                      </tr>
                    </thead>
                    <tbody>
                      {signals.map((s) => {
                        const id = s.signal_id || s.symbol;
                        const isOpen = open === id;
                        return (
                          <SignalRows
                            key={id}
                            signal={s}
                            isOpen={isOpen}
                            onToggle={() => setOpen(isOpen ? null : id)}
                          />
                        );
                      })}
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

function SignalRows({ signal: s, isOpen, onToggle }) {
  return (
    <>
      <tr
        className={`clickable ${isOpen ? 'expanded' : ''}`}
        onClick={onToggle}
        aria-expanded={isOpen}
      >
        <td>
          <span className="expand-caret">▸</span>
        </td>
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
        <td className="muted small" style={{ maxWidth: 320 }}>
          {s.reason || '—'}
        </td>
        <td className="muted small" style={{ whiteSpace: 'nowrap' }}>
          {formatDateTime(s.created_at)}
        </td>
      </tr>
      {isOpen ? (
        <tr className="detail-row">
          <td colSpan={9}>
            <SignalDetail s={s} />
          </td>
        </tr>
      ) : null}
    </>
  );
}

function SignalDetail({ s }) {
  const snap = s.data_snapshot || {};
  const allWarnings = [
    ...(s.warnings || []),
    ...(s.strategy_results || []).flatMap((r) => r.warnings || []),
  ];
  const allRiskFlags = (s.strategy_results || []).flatMap((r) => r.risk_flags || []);

  return (
    <div className="detail-pane stack" style={{ gap: 16 }}>
      <div className="grid cols-3">
        <KV label="Final recommendation" value={<LabelPill label={s.label} />} />
        <KV label="Final score" value={<span className="num">{formatScore(s.score)} / 100</span>} />
        <KV
          label="Led to paper trade"
          value={
            s.led_to_paper_trade ? (
              <span className="pill buy">YES · PAPER</span>
            ) : (
              <span className="pill neutral">NO</span>
            )
          }
        />
        <KV label="Estimated cost" value={<span className="num">{formatINR(s.estimated_cost)}</span>} />
        <KV label="Data quality" value={<span className="tag">{s.data_quality || '—'}</span>} />
        <KV label="Market regime" value={<span className="tag">{s.market_regime || '—'}</span>} />
      </div>

      <div>
        <div className="card-head" style={{ padding: '0 0 8px', border: 'none' }}>
          <h3 style={{ fontSize: 14 }}>Strategy breakdown</h3>
        </div>
        <StrategyBreakdown
          results={s.strategy_results || []}
          conflicts={s.conflict_warnings || []}
        />
      </div>

      {(allWarnings.length > 0 || allRiskFlags.length > 0) && (
        <div className="grid cols-2">
          {allWarnings.length > 0 ? (
            <div className="callout warn">
              <strong>Warnings</strong>
              <ul className="clean small" style={{ marginTop: 6 }}>
                {[...new Set(allWarnings)].map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {allRiskFlags.length > 0 ? (
            <div className="callout danger">
              <strong>Risk flags</strong>
              <ul className="clean small" style={{ marginTop: 6 }}>
                {[...new Set(allRiskFlags)].map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      )}

      <div>
        <div className="card-head" style={{ padding: '0 0 8px', border: 'none' }}>
          <h3 style={{ fontSize: 14 }}>Data snapshot</h3>
        </div>
        <dl className="kv">
          <dt>Price</dt>
          <dd className="num">{formatINR(snap.price)}</dd>
          <dt>Change</dt>
          <dd className="num">{snap.change_pct != null ? `${snap.change_pct}%` : '—'}</dd>
          <dt>Graph points</dt>
          <dd className="num">{snap.graph_points ?? '—'}</dd>
          <dt>Headlines</dt>
          <dd className="num">{snap.headlines_count ?? '—'}</dd>
          <dt>Extracted at</dt>
          <dd>{formatDateTime(snap.extracted_at)}</dd>
        </dl>
      </div>
    </div>
  );
}

function KV({ label, value }) {
  return (
    <div>
      <div className="label dim small">{label}</div>
      <div style={{ marginTop: 5 }}>{value}</div>
    </div>
  );
}
