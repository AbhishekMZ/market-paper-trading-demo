# 📄 Paper Trading Report — 2026-06-24 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_ON` — Benchmarks up 1.26% on average — risk-on.

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
ICICIBANK.NS(73.8), SBIN.NS(67.0), AXISBANK.NS(66.4)

## 🚫 Do-not-buy
BHARTIARTL.NS(49.9), INFY.NS(48.1), RELIANCE.NS(44.7), TCS.NS(42.6), ITC.NS(41.2)

## 🧠 Strategy contribution summary
- trend_following: avg 45/100 (weight 20)
- relative_strength: avg 59/100 (weight 20)
- mean_reversion _(display-only)_: avg 47/100 (weight 0)
- breakout _(display-only)_: avg 59/100 (weight 0)
- news_event_risk: avg 57/100 (weight 15)
- volatility_risk: avg 42/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- LT.NS: Disagreement: ['trend_following', 'news_event_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- BHARTIARTL.NS: Disagreement: ['news_event_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- INFY.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- RELIANCE.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- TCS.NS: Disagreement: ['relative_strength'] positive vs ['trend_following', 'volatility_risk', 'portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- ICICIBANK.NS (WATCH, 73.8): Final 73.8/100 -> WATCH [regime RISK_ON]. Top: relative_strength=95, trend_following=89, portfolio_fit=80.
- SBIN.NS (WATCH, 67.0): Final 67.0/100 -> WATCH [regime RISK_ON]. Top: trend_following=88, portfolio_fit=80, volatility_risk=64.
- AXISBANK.NS (WATCH, 66.4): Final 66.4/100 -> WATCH [regime RISK_ON]. Top: trend_following=88, portfolio_fit=80, relative_strength=68.
- HDFCBANK.NS (NO_ACTION, 62.9): Final 62.9/100 -> NO_ACTION [regime RISK_ON]. Top: relative_strength=89, portfolio_fit=80, news_event_risk=53.
- LT.NS (NO_ACTION, 53.3): Final 53.3/100 -> NO_ACTION [regime RISK_ON]. Top: trend_following=76, news_event_risk=70, volatility_risk=43. Disagreement: ['trend_following', 'news_event_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- BHARTIARTL.NS (DO_NOT_BUY, 49.9): Final 49.9/100 -> DO_NOT_BUY [regime RISK_ON]. Top: portfolio_fit=80, news_event_risk=75, volatility_risk=58. Disagreement: ['news_event_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- INFY.NS (DO_NOT_BUY, 48.1): Final 48.1/100 -> DO_NOT_BUY [regime RISK_ON]. Top: relative_strength=96, portfolio_fit=80, news_event_risk=53. Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- RELIANCE.NS (DO_NOT_BUY, 44.7): Final 44.7/100 -> DO_NOT_BUY [regime RISK_ON]. Top: portfolio_fit=80, volatility_risk=56, news_event_risk=41. Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 36 · total this month: 156 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2109 exceeds per-trade cap ₹2000.
- Share price ₹4182 exceeds per-trade cap ₹2000.
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