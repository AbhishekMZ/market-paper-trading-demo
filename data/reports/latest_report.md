# 📄 Paper Trading Report — 2026-07-01 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_ON` — Benchmarks up 0.72% on average — risk-on.

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
SBIN.NS(75.0), AXISBANK.NS(71.8), ICICIBANK.NS(66.9), BHARTIARTL.NS(66.6)

## 🚫 Do-not-buy
LT.NS(44.0), TCS.NS(30.8), INFY.NS(30.7)

## 🧠 Strategy contribution summary
- trend_following: avg 61/100 (weight 20)
- relative_strength: avg 43/100 (weight 20)
- mean_reversion _(display-only)_: avg 48/100 (weight 0)
- breakout _(display-only)_: avg 55/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 45/100 (weight 15)
- portfolio_fit: avg 70/100 (weight 10)

## ❗ Strategy conflicts
- ITC.NS: Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- HDFCBANK.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- RELIANCE.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- TCS.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength', 'volatility_risk'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- SBIN.NS (WATCH, 75.0): Final 75.0/100 -> WATCH [regime RISK_ON]. Top: trend_following=90, relative_strength=85, portfolio_fit=80.
- AXISBANK.NS (WATCH, 71.8): Final 71.8/100 -> WATCH [regime RISK_ON]. Top: trend_following=88, portfolio_fit=80, relative_strength=78.
- ICICIBANK.NS (WATCH, 66.9): Final 66.9/100 -> WATCH [regime RISK_ON]. Top: trend_following=93, portfolio_fit=80, news_event_risk=65.
- BHARTIARTL.NS (WATCH, 66.6): Final 66.6/100 -> WATCH [regime RISK_ON]. Top: portfolio_fit=80, trend_following=73, news_event_risk=65.
- ITC.NS (HOLD, 64.6): Final 64.6/100 -> HOLD [regime RISK_ON]. Top: trend_following=78, news_event_risk=65, volatility_risk=65. Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- HDFCBANK.NS (NO_ACTION, 62.0): Final 62.0/100 -> NO_ACTION [regime RISK_ON]. Top: trend_following=89, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- RELIANCE.NS (NO_ACTION, 58.8): Final 58.8/100 -> NO_ACTION [regime RISK_ON]. Top: portfolio_fit=80, news_event_risk=65, relative_strength=63. Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- LT.NS (DO_NOT_BUY, 44.0): Final 44.0/100 -> DO_NOT_BUY [regime RISK_ON]. Top: news_event_risk=65, trend_following=60, volatility_risk=43.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 36 · total this month: 36 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹4093 exceeds per-trade cap ₹2000.
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