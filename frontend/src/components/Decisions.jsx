// Decision Quality tab — does the system actually make good decisions?
// Composes the five evaluation panels; all read public/data/decision_quality.json
// and show a clean empty / "not enough data yet" state on a fresh demo.
import { useData } from '../hooks/useData.js';
import { DataGate } from './ui.jsx';
import DecisionQuality from './DecisionQuality.jsx';
import EvidenceSummary from './EvidenceSummary.jsx';
import BenchmarkComparison from './BenchmarkComparison.jsx';
import StrategyLeaderboard from './StrategyLeaderboard.jsx';
import ShadowSignals from './ShadowSignals.jsx';
import ThresholdAnalysis from './ThresholdAnalysis.jsx';

export default function Decisions() {
  const dq = useData('decision_quality.json');

  return (
    <>
      <DataGate
        file="decision_quality.json"
        state={dq}
        emptyWhen={(d) => !d || d.enabled === false}
      >
        {(d) => (
          <EvidenceSummary
            summary={d.evidence_summary}
            metrics={d.metrics}
            readiness={d.readiness}
          />
        )}
      </DataGate>
      <DecisionQuality />
      <BenchmarkComparison />
      <StrategyLeaderboard />
      <ShadowSignals />
      <ThresholdAnalysis />
    </>
  );
}
