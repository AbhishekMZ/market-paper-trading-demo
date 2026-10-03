// Per-stock "why" card for the Why view. Renders the engine's own verdict, the
// news/data/budget gates, and (collapsible) the full per-strategy vote breakdown.
import { useState } from 'react';
import { Card, LabelPill } from './ui.jsx';
import { formatScore, formatINR, formatConfidence } from '../lib/format.js';
import { orderStrategyVotes } from '../lib/narrative.js';
import StrategyBreakdown from './StrategyBreakdown.jsx';

// One-line plain-English verdict derived from the signal's label.
function verdict(s) {
  if (s.led_to_paper_trade || s.label === 'BUY_SMALL_PAPER')
    return `${formatScore(s.score)} → bought on paper`;
  if (s.label === 'WATCH') return `${formatScore(s.score)} → WATCH (buy bar not met)`;
  if (s.label === 'NO_ACTION') return `${formatScore(s.score)} → no action`;
  if (s.label === 'DO_NOT_BUY' || s.label === 'HIGH_RISK_IGNORE')
    return `${formatScore(s.score)} → avoided`;
  return `${formatScore(s.score)} / 100`;
}

function Gate({ label, value, tone = 'neutral' }) {
  return (
    <span className="gate">
      <span className="gate-label">{label}</span>
      <span className={`pill ${tone}`}>{value}</span>
    </span>
  );
}

function sentimentTone(sentiment) {
  if (sentiment === 'NEGATIVE') return 'danger';
  if (sentiment === 'POSITIVE') return 'ok';
  return 'neutral';
}

/** Phase 2 C: sentiment · confidence · sources-agree from existing signal fields. */
function SentimentLine({ signal: s }) {
  const sentiment = s.news_sentiment;
  if (sentiment == null || sentiment === '') return null;
  const conf = formatConfidence(s.news_sentiment_confidence);
  const agree =
    s.news_sentiment_sources_agree == null
      ? 'sources —'
      : s.news_sentiment_sources_agree
        ? 'sources agree'
        : 'sources disagree';
  return (
    <p className="muted small trace-sentiment" style={{ margin: 0 }}>
      Sentiment:{' '}
      <span className={`pill ${sentimentTone(sentiment)}`}>{sentiment}</span>
      {' · '}
      confidence {conf}
      {' · '}
      {agree}
    </p>
  );
}

export default function DecisionTrace({ signal: s, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const ordered = orderStrategyVotes(s.strategy_results || []);
  const newsBlocks = s.news_blocks_buy;
  const dataOk = (s.data_quality_verdict || 'OK') === 'OK';

  return (
    <Card
      title={`${s.symbol}${s.name ? ' · ' + s.name : ''}`}
      headRight={<LabelPill label={s.label} />}
    >
      <div className="card-pad stack" style={{ gap: 12 }}>
        <div className="trace-verdict">{verdict(s)}</div>

        <div className="gate-row">
          <Gate
            label="News"
            value={newsBlocks ? 'BLOCKS BUY' : s.news_risk_level || 'OK'}
            tone={newsBlocks ? 'danger' : 'ok'}
          />
          <Gate label="Data" value={s.data_quality_verdict || 'OK'} tone={dataOk ? 'ok' : 'warn'} />
          <Gate
            label="Est. cost"
            value={s.estimated_cost != null ? formatINR(s.estimated_cost) : '—'}
            tone="neutral"
          />
          <Gate
            label="Paper trade"
            value={s.led_to_paper_trade ? 'YES' : 'NO'}
            tone={s.led_to_paper_trade ? 'buy' : 'neutral'}
          />
        </div>

        <SentimentLine signal={s} />

        {s.news_top_headline ? (
          <p className="muted small" style={{ margin: 0 }}>
            Top headline: {s.news_top_headline}
          </p>
        ) : null}

        {s.hist_context_available ? (
          <p className="muted small why-context" style={{ margin: 0 }}>
            {s.hist_vol_percentile != null && (
              <span>vol {Math.round(s.hist_vol_percentile)}th pctile</span>
            )}
            {s.hist_range_position != null && (
              <span> · range {(s.hist_range_position * 100).toFixed(0)}% of 2y</span>
            )}
            {s.hist_beta != null && <span> · β {Number(s.hist_beta).toFixed(2)}</span>}
            {s.hist_context_flags?.length > 0 && (
              <span> · context: {s.hist_context_flags.join(', ')}</span>
            )}
          </p>
        ) : null}

        <button className="trace-toggle" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
          {open ? 'Hide' : 'Show'} strategy votes ({ordered.length})
        </button>

        {open ? (
          <StrategyBreakdown results={ordered} conflicts={s.conflict_warnings || []} />
        ) : null}
      </div>
    </Card>
  );
}
