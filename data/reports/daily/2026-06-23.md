# 📄 Paper Trading Report — 2026-06-23 (mid)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_OFF` — Benchmarks down -0.87% on average — risk-off. New buys blocked.

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
HDFCBANK.NS(38.7), ITC.NS(38.3), RELIANCE.NS(37.3), TCS.NS(18.2), INFY.NS(14.7)

## 🧠 Strategy contribution summary
- trend_following: avg 44/100 (weight 20)
- relative_strength: avg 47/100 (weight 20)
- mean_reversion _(display-only)_: avg 46/100 (weight 0)
- breakout _(display-only)_: avg 57/100 (weight 0)
- news_event_risk: avg 56/100 (weight 15)
- volatility_risk: avg 43/100 (weight 15)
- portfolio_fit: avg 15/100 (weight 10)

## ❗ Strategy conflicts
- ICICIBANK.NS: Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- LT.NS: Disagreement: ['trend_following', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- BHARTIARTL.NS: Disagreement: ['news_event_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS: Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- AXISBANK.NS: Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- ICICIBANK.NS (NO_ACTION, 57.2): Final 57.2/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=88, relative_strength=72, volatility_risk=58. Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- LT.NS (NO_ACTION, 52.7): Final 52.7/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=76, news_event_risk=70, relative_strength=60. Disagreement: ['trend_following', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- BHARTIARTL.NS (NO_ACTION, 52.5): Final 52.5/100 -> NO_ACTION [regime RISK_OFF]. Top: news_event_risk=75, relative_strength=60, trend_following=59. Disagreement: ['news_event_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS (NO_ACTION, 52.4): Final 52.4/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=87, volatility_risk=65, news_event_risk=53. Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- AXISBANK.NS (NO_ACTION, 51.8): Final 51.8/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=75, relative_strength=70, volatility_risk=55. Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- HDFCBANK.NS (DO_NOT_BUY, 38.7): Final 38.7/100 -> DO_NOT_BUY [regime RISK_OFF]. Top: news_event_risk=53, relative_strength=44, volatility_risk=44.
- ITC.NS (DO_NOT_BUY, 38.3): Final 38.3/100 -> DO_NOT_BUY [regime RISK_OFF]. Top: news_event_risk=65, relative_strength=60, volatility_risk=49.
- RELIANCE.NS (DO_NOT_BUY, 37.3): Final 37.3/100 -> DO_NOT_BUY [regime RISK_OFF]. Top: relative_strength=59, volatility_risk=56, news_event_risk=41.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 96 · total this month: 96 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Daily buy limit reached.
- Market regime: RISK_OFF.
- Share price ₹2066 exceeds per-trade cap ₹2000.
- Share price ₹4185 exceeds per-trade cap ₹2000.
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