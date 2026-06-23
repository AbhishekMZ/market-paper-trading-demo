# 📄 Paper Trading Report — 2026-06-23 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_OFF` — Benchmarks down -1.23% on average — risk-off. New buys blocked.

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
ITC.NS(40.0), HDFCBANK.NS(37.2), RELIANCE.NS(33.5), TCS.NS(18.2), INFY.NS(14.7)

## 🧠 Strategy contribution summary
- trend_following: avg 41/100 (weight 20)
- relative_strength: avg 46/100 (weight 20)
- mean_reversion _(display-only)_: avg 46/100 (weight 0)
- breakout _(display-only)_: avg 52/100 (weight 0)
- news_event_risk: avg 56/100 (weight 15)
- volatility_risk: avg 42/100 (weight 15)
- portfolio_fit: avg 15/100 (weight 10)

## ❗ Strategy conflicts
- AXISBANK.NS: Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- LT.NS: Disagreement: ['trend_following', 'relative_strength', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- BHARTIARTL.NS: Disagreement: ['news_event_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS: Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- ICICIBANK.NS: Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- ITC.NS: Disagreement: ['relative_strength'] positive vs ['trend_following', 'portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- AXISBANK.NS (NO_ACTION, 56.1): Final 56.1/100 -> NO_ACTION [regime RISK_OFF]. Top: relative_strength=88, trend_following=78, volatility_risk=55. Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- LT.NS (NO_ACTION, 53.5): Final 53.5/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=75, news_event_risk=70, relative_strength=66. Disagreement: ['trend_following', 'relative_strength', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- BHARTIARTL.NS (NO_ACTION, 51.7): Final 51.7/100 -> NO_ACTION [regime RISK_OFF]. Top: news_event_risk=75, relative_strength=59, volatility_risk=59. Disagreement: ['news_event_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS (NO_ACTION, 51.2): Final 51.2/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=87, volatility_risk=63, news_event_risk=53. Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- ICICIBANK.NS (NO_ACTION, 50.8): Final 50.8/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=76, volatility_risk=57, news_event_risk=53. Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- ITC.NS (DO_NOT_BUY, 40.0): Final 40.0/100 -> DO_NOT_BUY [regime RISK_OFF]. Top: relative_strength=68, news_event_risk=65, volatility_risk=49. Disagreement: ['relative_strength'] positive vs ['trend_following', 'portfolio_fit'] negative.
- HDFCBANK.NS (DO_NOT_BUY, 37.2): Final 37.2/100 -> DO_NOT_BUY [regime RISK_OFF]. Top: news_event_risk=53, volatility_risk=43, relative_strength=42.
- RELIANCE.NS (HIGH_RISK_IGNORE, 33.5): Final 33.5/100 -> HIGH_RISK_IGNORE [regime RISK_OFF]. Top: volatility_risk=55, relative_strength=47, news_event_risk=41.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 120 · total this month: 120 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Daily buy limit reached.
- Market regime: RISK_OFF.
- Share price ₹2060 exceeds per-trade cap ₹2000.
- Share price ₹4179 exceeds per-trade cap ₹2000.
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