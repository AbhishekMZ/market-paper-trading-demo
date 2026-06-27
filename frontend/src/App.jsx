import { useState } from 'react';
import { useData } from './hooks/useData.js';
import { formatDateTime } from './lib/format.js';

import Today from './views/Today.jsx';
import Why from './views/Why.jsx';
import TrackRecord from './views/TrackRecord.jsx';

const TABS = [
  { id: 'today', label: 'Today' },
  { id: 'why', label: 'Why' },
  { id: 'track', label: 'Track Record' },
];

function PaperBanner() {
  return (
    <div className="paper-banner">
      <div className="container">
        <span className="dot" />
        <span>PAPER TRADING ONLY — fake money. Live trading DISABLED.</span>
      </div>
    </div>
  );
}

function StatusStrip({ report }) {
  const exec = report?.execution || {};
  const generatedAt = report?.generated_at;
  return (
    <div className="status-strip">
      <span className="status-item">
        <span className="status-led info" /> Mode = <b>PAPER</b>
      </span>
      <span className="status-item">
        <span className="status-led info" /> Broker adapter = <b>{exec.broker_adapter || 'paper'}</b>
      </span>
      <span className="status-item">
        <span className="status-led off" /> Live trading = <b>DISABLED</b>
      </span>
      <span className="status-item">
        <span className="status-led off" /> Angel One = <b>DISABLED</b>
      </span>
      <span className="status-item">
        <span className="status-led ok" /> Last updated ={' '}
        <b>{generatedAt ? formatDateTime(generatedAt) : '—'}</b>
      </span>
    </div>
  );
}

export default function App() {
  const [active, setActive] = useState('today');
  const [focusSymbol, setFocusSymbol] = useState(null);

  // The report is the spine of the dashboard; share it across views.
  const report = useData('latest_report.json');

  function goToWhy(symbol) {
    setFocusSymbol(symbol);
    setActive('why');
  }

  return (
    <div className="app-shell">
      <PaperBanner />

      <header className="app-header">
        <div className="container">
          <div className="brand">
            <div className="brand-mark">₹</div>
            <div>
              <h1>Paper Trading Desk</h1>
              <p>Indian equities · multi-strategy signal engine · fake-money demo</p>
            </div>
          </div>
          <StatusStrip report={report.data} />
        </div>
      </header>

      <nav className="tabs" aria-label="Sections">
        <div className="container">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`tab-btn ${active === t.id ? 'active' : ''}`}
              onClick={() => setActive(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="content">
        <div className="container">
          {active === 'today' && <Today report={report} onSelectSymbol={goToWhy} />}
          {active === 'why' && <Why report={report} focusSymbol={focusSymbol} />}
          {active === 'track' && <TrackRecord report={report} />}
        </div>
      </main>

      <footer className="app-footer">
        <div className="container">
          Demo dashboard. Numbers are simulated paper-trading results — no real orders are ever
          placed, no broker is connected, and no funds are at risk. Not investment advice.
        </div>
      </footer>
    </div>
  );
}
