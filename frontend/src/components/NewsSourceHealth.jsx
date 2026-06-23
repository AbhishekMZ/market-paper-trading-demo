// News sources — which providers fed the news layer this run and their
// operational notes (cost, reliability, and degradation behavior).
import { useData } from '../hooks/useData.js';
import { Card, Stat, Pill, DataGate } from './ui.jsx';
import { formatDateTime } from '../lib/format.js';

export default function NewsSourceHealth() {
  const health = useData('news_health.json');

  return (
    <div className="grid">
      <Card title="News sources" sub="Providers feeding the news risk layer">
        <DataGate file="news_health.json" state={health}>
          {(news) => (
            <>
              <div className="stat-row">
                <Stat label="Providers used" value={(news.providers_used && news.providers_used.join(', ')) || '—'} />
                <Stat label="Symbols with news" value={news.symbols_with_news ?? 0} />
                <Stat label="Total items" value={news.total_items ?? 0} />
                <Stat label="Alerts this run" value={news.alerts_this_run ?? 0} />
                <Stat label="Last run" value={news.last_run ? formatDateTime(news.last_run) : '—'} />
              </div>
              <div className="muted small" style={{ marginTop: 8 }}>
                <div>yfinance headlines — unofficial source, best-effort.</div>
                <div>GDELT 2.0 Doc API — free, no key; degrades to no-news on failure.</div>
                <div>
                  NewsAPI —{' '}
                  <Pill tone="neutral">
                    {news.newsapi_enabled ? 'enabled' : 'disabled (no key; ₹0-cost v1)'}
                  </Pill>
                </div>
              </div>
            </>
          )}
        </DataGate>
      </Card>
    </div>
  );
}
