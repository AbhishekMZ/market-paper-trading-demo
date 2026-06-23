# 📄 Paper Trading Report — 2026-06-23 (mid)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (-0.38%) — neutral regime.

## 💰 Portfolio (fake money)
- Total value: **₹10,091.50** (started ₹10,000.00)
- Cash: ₹8,474.74 · Holdings: ₹1,616.76
- Realized P&L: ₹0.00 · Unrealized: ₹91.50
- Total return: +0.91% · Max drawdown: +0.00%
- Monthly budget: deployed ₹1,525.26 / ₹10,000.00 · buys 1/5
- **Cost-adjusted** net realized: ₹0.00 (est. costs ₹0.00)

## ✅ Top paper-buy candidates
- None this checkpoint.

## 👀 Watchlist
None.

## 🚫 Do-not-buy
HDFCBANK.NS(44.9), ITC.NS(42.7), RELIANCE.NS(41.4), TCS.NS(22.2), INFY.NS(18.6)

## 🧠 Strategy contribution summary
- trend_following: avg 47/100 (weight 20)
- relative_strength: avg 48/100 (weight 20)
- mean_reversion _(display-only)_: avg 46/100 (weight 0)
- breakout _(display-only)_: avg 59/100 (weight 0)
- news_event_risk: avg 56/100 (weight 15)
- volatility_risk: avg 43/100 (weight 15)
- portfolio_fit: avg 15/100 (weight 10)

## ❗ Strategy conflicts
- ICICIBANK.NS: Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- LT.NS: Disagreement: ['trend_following', 'relative_strength', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- BHARTIARTL.NS: Disagreement: ['trend_following', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS: Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- AXISBANK.NS: Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- ICICIBANK.NS (NO_ACTION, 63.7): [DATA DATA_ANOMALY] Final 63.7/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=90, relative_strength=79, news_event_risk=58. Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- LT.NS (NO_ACTION, 61.0): [DATA DATA_ANOMALY] Final 61.0/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=87, relative_strength=72, news_event_risk=70. Disagreement: ['trend_following', 'relative_strength', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- BHARTIARTL.NS (NO_ACTION, 57.9): [DATA DATA_ANOMALY] Final 57.9/100 -> NO_ACTION [regime NEUTRAL]. Top: news_event_risk=75, trend_following=66, relative_strength=61. Disagreement: ['trend_following', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS (NO_ACTION, 55.8): [DATA DATA_ANOMALY] Final 55.8/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=87, volatility_risk=66, news_event_risk=53. Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- AXISBANK.NS (NO_ACTION, 55.4): [DATA DATA_ANOMALY] Final 55.4/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=78, relative_strength=65, volatility_risk=55. Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- HDFCBANK.NS (DO_NOT_BUY, 44.9): [DATA DATA_ANOMALY] Final 44.9/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: news_event_risk=53, relative_strength=49, volatility_risk=45.
- ITC.NS (DO_NOT_BUY, 42.7): [DATA DATA_ANOMALY] Final 42.7/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: news_event_risk=65, relative_strength=58, volatility_risk=49.
- RELIANCE.NS (DO_NOT_BUY, 41.4): [DATA DATA_ANOMALY] Final 41.4/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: volatility_risk=56, relative_strength=56, news_event_risk=41.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 84 · total this month: 84 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Daily buy limit reached.
- DataQuality:DATA_ANOMALY
- Share price ₹2068 exceeds per-trade cap ₹2000.
- Share price ₹4227 exceeds per-trade cap ₹2000.
- price source changed today: unknown -> history.close.
- 11 data-quality incident(s) this run — see Data Health.

## 🔭 Future-readiness checklist
- ✅ Phase 1: Paper trading running (email + GitHub Pages, ₹0 cost)
- ✅ BrokerAdapter abstraction in place (paper enabled, Angel One stub disabled)
- ✅ Live trading disabled by config
- ✅ Angel One adapter disabled by config
- ✅ Manual approval required for any real order
- ⬜ ≥1 strategy accepted for manual review (post-validation)
- ⬜ Phase 2: Manual-approval real trading (future)
- ⬜ Phase 3: Limited real execution, delivery+limit only (future)
- ⬜ Phase 4: Controlled automation w/ kill switch (future)

---
_This is a fake-money paper-trading demo. No real orders were placed. Not investment advice._