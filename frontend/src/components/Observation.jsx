// Observation tab — lightweight between-checkpoint monitoring + escalation.
// Composes the five panels; each self-fetches its own public/data file and shows
// a clean empty state until an observation run has populated it.
import ObservationPanel from './ObservationPanel.jsx';
import ActionReadiness from './ActionReadiness.jsx';
import ActiveWatchlist from './ActiveWatchlist.jsx';
import EscalationQueue from './EscalationQueue.jsx';
import TriggerHistory from './TriggerHistory.jsx';

export default function Observation() {
  return (
    <>
      <ObservationPanel />
      <ActionReadiness />
      <ActiveWatchlist />
      <EscalationQueue />
      <TriggerHistory />
    </>
  );
}
