// Decision Quality tab — does the system actually make good decisions?
// Composes the five evaluation panels; all read public/data/decision_quality.json
// and show a clean empty / "not enough data yet" state on a fresh demo.
import DecisionQuality from './DecisionQuality.jsx';
import BenchmarkComparison from './BenchmarkComparison.jsx';
import StrategyLeaderboard from './StrategyLeaderboard.jsx';
import ShadowSignals from './ShadowSignals.jsx';
import ThresholdAnalysis from './ThresholdAnalysis.jsx';

export default function Decisions() {
  return (
    <>
      <DecisionQuality />
      <BenchmarkComparison />
      <StrategyLeaderboard />
      <ShadowSignals />
      <ThresholdAnalysis />
    </>
  );
}
