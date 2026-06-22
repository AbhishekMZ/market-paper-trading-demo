import { humanizeKey, signalTone, formatConfidence } from '../lib/format.js';

function clamp(n) {
  const v = Number(n);
  if (Number.isNaN(v)) return 0;
  return Math.max(0, Math.min(100, v));
}

/**
 * Per-strategy contribution view from a signal's strategy_results array.
 * Each item: { strategy_name, score_contribution, confidence, signal, reason,
 *   data_used, warnings, risk_flags, contributes_to_score, display_only,
 *   is_valid, error }.
 *
 * Props:
 *  - results: strategy_results array
 *  - conflicts: optional conflict_warnings array
 *  - compact: render a tighter inline element (hides reasons/data)
 */
export default function StrategyBreakdown({ results = [], conflicts = [], compact = false }) {
  if (!Array.isArray(results) || results.length === 0) {
    return <p className="muted small">No per-strategy breakdown available.</p>;
  }

  return (
    <div className="stack" style={{ gap: 12 }}>
      <div className="strat-list">
        {results.map((r, i) => {
          const tone = signalTone(r.signal);
          const score = clamp(r.score_contribution);
          const dim = r.display_only || !r.contributes_to_score;
          const flags = [];
          if (r.display_only) flags.push({ cls: 'exp', text: 'DISPLAY-ONLY' });
          if (!r.contributes_to_score && !r.display_only)
            flags.push({ cls: 'flag', text: 'NOT WEIGHTED' });
          if (r.is_valid === false) flags.push({ cls: 'err', text: 'INVALID' });
          if (r.error) flags.push({ cls: 'err', text: 'ERROR' });
          (r.risk_flags || []).forEach((rf) => flags.push({ cls: 'risk', text: rf }));
          (r.warnings || []).forEach((w) => flags.push({ cls: 'warn', text: w }));

          return (
            <div className="strat-row" key={r.strategy_name || i}>
              <div className="name">
                {humanizeKey(r.strategy_name)}
                {flags.slice(0, compact ? 1 : flags.length).map((f, j) => (
                  <span className={`flag ${f.cls}`} key={j} title={f.text}>
                    {f.text.length > 26 ? `${f.text.slice(0, 24)}…` : f.text}
                  </span>
                ))}
              </div>
              <div className="strat-track" title={`signal: ${r.signal || '—'}`}>
                <div className={`strat-fill ${tone} ${dim ? 'dim' : ''}`} style={{ width: `${score}%` }} />
              </div>
              <div className="strat-score">
                {score.toFixed(0)}
                {!compact && r.confidence != null ? (
                  <span className="dim"> · {formatConfidence(r.confidence)}</span>
                ) : null}
              </div>
              {!compact && r.reason ? <div className="strat-reason">{r.reason}</div> : null}
            </div>
          );
        })}
      </div>

      {Array.isArray(conflicts) && conflicts.length > 0 ? (
        <div className="callout warn">
          <strong>Conflict warnings</strong>
          <ul className="clean small" style={{ marginTop: 6 }}>
            {conflicts.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
