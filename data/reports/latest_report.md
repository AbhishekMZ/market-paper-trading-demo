# 📄 Paper Trading Report — 2026-07-10 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_ON` — Benchmarks up 1.20% on average — risk-on.

## 💰 Portfolio (fake money)
- Total value: **₹10,091.50** (started ₹10,000.00)
- Cash: ₹8,474.74 · Holdings: ₹1,616.76
- Realized P&L: ₹0.00 · Unrealized: ₹91.50
- Total return: +0.91% · Max drawdown: +0.00%
- Monthly budget: deployed ₹0.00 / ₹10,000.00 · buys 0/100
- **Cost-adjusted** net realized: ₹0.00 (est. costs ₹0.00)

## ✅ Top paper-buy candidates
- None this checkpoint.

## 👀 Watchlist
RELIANCE.NS(70.2), ICICIBANK.NS(70.0), SBIN.NS(65.5)

## 🚫 Do-not-buy
ITC.NS(48.0), INFY.NS(43.8), TCS.NS(39.6)

## 🧠 Strategy contribution summary
- trend_following: avg 57/100 (weight 20)
- relative_strength: avg 53/100 (weight 20)
- mean_reversion _(display-only)_: avg 48/100 (weight 0)
- breakout _(display-only)_: avg 52/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 44/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- BHARTIARTL.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- ITC.NS: Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- INFY.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- RELIANCE.NS (WATCH, 70.2): Final 70.2/100 -> WATCH [regime RISK_ON]. Top: portfolio_fit=80, trend_following=79, relative_strength=79.
- ICICIBANK.NS (WATCH, 70.0): Final 70.0/100 -> WATCH [regime RISK_ON]. Top: trend_following=93, portfolio_fit=80, news_event_risk=65.
- SBIN.NS (WATCH, 65.5): Final 65.5/100 -> WATCH [regime RISK_ON]. Top: portfolio_fit=80, trend_following=72, news_event_risk=65.
- HDFCBANK.NS (NO_ACTION, 64.1): Final 64.1/100 -> NO_ACTION [regime RISK_ON]. Top: trend_following=89, portfolio_fit=80, news_event_risk=65.
- AXISBANK.NS (NO_ACTION, 63.0): Final 63.0/100 -> NO_ACTION [regime RISK_ON]. Top: portfolio_fit=80, relative_strength=75, news_event_risk=65.
- BHARTIARTL.NS (NO_ACTION, 59.2): Final 59.2/100 -> NO_ACTION [regime RISK_ON]. Top: trend_following=90, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- LT.NS (NO_ACTION, 52.8): Final 52.8/100 -> NO_ACTION [regime RISK_ON]. Top: news_event_risk=65, relative_strength=63, trend_following=48.
- ITC.NS (DO_NOT_BUY, 48.0): Final 48.0/100 -> DO_NOT_BUY [regime RISK_ON]. Top: volatility_risk=66, news_event_risk=65, trend_following=37. Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 36 · total this month: 288 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2069 exceeds per-trade cap ₹2000.
- Share price ₹3946 exceeds per-trade cap ₹2000.
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