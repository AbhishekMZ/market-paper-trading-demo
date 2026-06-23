# 📄 Paper Trading Report — 2026-06-23 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_OFF` — Benchmarks down -0.91% on average — risk-off. New buys blocked.

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
ITC.NS(39.5), HDFCBANK.NS(37.0), RELIANCE.NS(34.7), TCS.NS(18.6), INFY.NS(14.9)

## 🧠 Strategy contribution summary
- trend_following: avg 44/100 (weight 20)
- relative_strength: avg 46/100 (weight 20)
- mean_reversion _(display-only)_: avg 46/100 (weight 0)
- breakout _(display-only)_: avg 57/100 (weight 0)
- news_event_risk: avg 56/100 (weight 15)
- volatility_risk: avg 43/100 (weight 15)
- portfolio_fit: avg 15/100 (weight 10)

## ❗ Strategy conflicts
- AXISBANK.NS: Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- LT.NS: Disagreement: ['trend_following', 'relative_strength', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- ICICIBANK.NS: Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- BHARTIARTL.NS: Disagreement: ['news_event_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS: Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- AXISBANK.NS (NO_ACTION, 57.3): Final 57.3/100 -> NO_ACTION [regime RISK_OFF]. Top: relative_strength=90, trend_following=82, volatility_risk=54. Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- LT.NS (NO_ACTION, 54.6): Final 54.6/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=79, news_event_risk=70, relative_strength=67. Disagreement: ['trend_following', 'relative_strength', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- ICICIBANK.NS (NO_ACTION, 53.4): Final 53.4/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=82, relative_strength=59, volatility_risk=58. Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- BHARTIARTL.NS (NO_ACTION, 51.1): Final 51.1/100 -> NO_ACTION [regime RISK_OFF]. Top: news_event_risk=75, volatility_risk=59, trend_following=58. Disagreement: ['news_event_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS (NO_ACTION, 50.7): Final 50.7/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=87, volatility_risk=64, news_event_risk=53. Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- ITC.NS (DO_NOT_BUY, 39.5): Final 39.5/100 -> DO_NOT_BUY [regime RISK_OFF]. Top: news_event_risk=65, relative_strength=64, volatility_risk=49.
- HDFCBANK.NS (DO_NOT_BUY, 37.0): Final 37.0/100 -> DO_NOT_BUY [regime RISK_OFF]. Top: news_event_risk=53, volatility_risk=44, relative_strength=38.
- RELIANCE.NS (HIGH_RISK_IGNORE, 34.7): Final 34.7/100 -> HIGH_RISK_IGNORE [regime RISK_OFF]. Top: volatility_risk=55, relative_strength=49, news_event_risk=41.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 108 · total this month: 108 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Daily buy limit reached.
- Market regime: RISK_OFF.
- Share price ₹2070 exceeds per-trade cap ₹2000.
- Share price ₹4198 exceeds per-trade cap ₹2000.
- 1 data-quality incident(s) this run — see Data Health.

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