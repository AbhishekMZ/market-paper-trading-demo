// "Why" view: a plain-English narrative of the run, then one DecisionTrace card
// per scanned stock (highest score first). When arriving from a Today row click,
// the matching card is expanded and scrolled into view.
import { useEffect, useRef } from 'react';
import { DataGate, Card } from '../components/ui.jsx';
import { runNarrative } from '../lib/narrative.js';
import DecisionTrace from '../components/DecisionTrace.jsx';

export default function Why({ report, focusSymbol }) {
  const focusRef = useRef(null);

  useEffect(() => {
    if (focusSymbol && focusRef.current) {
      focusRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [focusSymbol, report.data]);

  return (
    <DataGate file="latest_report.json" state={report}>
      {(data) => {
        const signals = (data.signals || [])
          .slice()
          .sort((a, b) => Number(b.score) - Number(a.score));
        const narrative = runNarrative(data);
        return (
          <div className="stack" style={{ gap: 18 }}>
            <div className="view-head">
              <h2>Why</h2>
              <p>
                What the engine decided this run and the reasoning behind each call —
                straight from the strategies that scored every stock.
              </p>
            </div>

            <Card title="What the engine did" sub={`${data.checkpoint} checkpoint`}>
              <div className="card-pad stack" style={{ gap: 8 }}>
                {narrative.map((line, i) => (
                  <p key={i} className="muted" style={{ margin: 0 }}>
                    {line}
                  </p>
                ))}
              </div>
            </Card>

            <div className="stack" style={{ gap: 14 }}>
              {signals.map((s) => {
                const isFocus = focusSymbol != null && s.symbol === focusSymbol;
                return (
                  <div key={s.signal_id || s.symbol} ref={isFocus ? focusRef : null}>
                    <DecisionTrace signal={s} defaultOpen={isFocus} />
                  </div>
                );
              })}
            </div>
          </div>
        );
      }}
    </DataGate>
  );
}
