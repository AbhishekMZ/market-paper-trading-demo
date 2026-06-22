import { useState } from 'react';
import { useData } from './hooks/useData.js';
import { formatDateTime } from './lib/format.js';

import Dashboard from './components/Dashboard.jsx';
import SignalTable from './components/SignalTable.jsx';
import Portfolio from './components/Portfolio.jsx';
import TradeHistory from './components/TradeHistory.jsx';
import AuditLog from './components/AuditLog.jsx';
import StrategyEvaluation from './components/StrategyEvaluation.jsx';
import ResearchHypotheses from './components/ResearchHypotheses.jsx';
import SettingsView from './components/SettingsView.jsx';
import ExecutionMode from './components/ExecutionMode.jsx';
import FutureReadiness from './components/FutureReadiness.jsx';

const TABS = [
  { id: 'dashboard', label: 'Dashboard', el: Dashboard },
  { id: 'signals', label: 'Signals', el: SignalTable },
  { id: 'portfolio', label: 'Portfolio', el: Portfolio },
  { id: 'trades', label: 'Trade History', el: TradeHistory },
  { id: 'audit', label: 'Audit Log', el: AuditLog },
  { id: 'evaluation', label: 'Strategy Eval', el: StrategyEvaluation },
  { id: 'research', label: 'Research', el: ResearchHypotheses },
  { id: 'execution', label: 'Execution Mode', el: ExecutionMode },
  { id: 'settings', label: 'Settings', el: SettingsView },
  { id: 'future', label: 'Future Readiness', el: FutureReadiness },
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
  const [active, setActive] = useState('dashboard');

  // The report is the spine of the dashboard; share it across views.
  const report = useData('latest_report.json');

  const ActiveView = TABS.find((t) => t.id === active)?.el || Dashboard;

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
          <ActiveView report={report} />
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
