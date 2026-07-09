# 📄 Paper Trading Report — 2026-07-09 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_ON` — Benchmarks up 0.62% on average — risk-on.

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
BHARTIARTL.NS(76.5), HDFCBANK.NS(67.5), ICICIBANK.NS(66.0)

## 🚫 Do-not-buy
LT.NS(46.1), TCS.NS(35.1), INFY.NS(30.7)

## 🧠 Strategy contribution summary
- trend_following: avg 52/100 (weight 20)
- relative_strength: avg 45/100 (weight 20)
- mean_reversion _(display-only)_: avg 50/100 (weight 0)
- breakout _(display-only)_: avg 50/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 44/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- AXISBANK.NS: Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- BHARTIARTL.NS (WATCH, 76.5): Final 76.5/100 -> WATCH [regime RISK_ON]. Top: relative_strength=98, trend_following=90, portfolio_fit=80.
- HDFCBANK.NS (WATCH, 67.5): Final 67.5/100 -> WATCH [regime RISK_ON]. Top: trend_following=89, portfolio_fit=80, news_event_risk=65.
- ICICIBANK.NS (WATCH, 66.0): Final 66.0/100 -> WATCH [regime RISK_ON]. Top: trend_following=93, portfolio_fit=80, news_event_risk=65.
- SBIN.NS (NO_ACTION, 62.6): Final 62.6/100 -> NO_ACTION [regime RISK_ON]. Top: portfolio_fit=80, news_event_risk=65, trend_following=61.
- RELIANCE.NS (NO_ACTION, 59.0): Final 59.0/100 -> NO_ACTION [regime RISK_ON]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=55.
- ITC.NS (HOLD, 56.7): Final 56.7/100 -> HOLD [regime RISK_ON]. Top: news_event_risk=65, volatility_risk=64, relative_strength=54.
- AXISBANK.NS (NO_ACTION, 51.5): Final 51.5/100 -> NO_ACTION [regime RISK_ON]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=52. Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- LT.NS (DO_NOT_BUY, 46.1): Final 46.1/100 -> DO_NOT_BUY [regime RISK_ON]. Top: news_event_risk=65, volatility_risk=40, trend_following=39.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 36 · total this month: 252 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2050 exceeds per-trade cap ₹2000.
- Share price ₹3886 exceeds per-trade cap ₹2000.
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