// News tab — the news risk overlay surfaced for the demo dashboard.
// Composes the four news panels. Each self-fetches its own public/data file
// and shows a clean empty state until a run has populated it.
import NewsRiskPanel from './NewsRiskPanel.jsx';
import NewsSourceHealth from './NewsSourceHealth.jsx';
import NewsAlerts from './NewsAlerts.jsx';
import NewsEvents from './NewsEvents.jsx';

export default function News() {
  return (
    <>
      <NewsRiskPanel />
      <NewsSourceHealth />
      <NewsAlerts />
      <NewsEvents />
    </>
  );
}
