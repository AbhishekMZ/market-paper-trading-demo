# 📄 Paper Trading Report — 2026-07-06 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_ON` — Benchmarks up 0.63% on average — risk-on.

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
HDFCBANK.NS(73.6), ICICIBANK.NS(71.1), RELIANCE.NS(70.2), BHARTIARTL.NS(68.0)

## 🚫 Do-not-buy
INFY.NS(35.1), TCS.NS(29.3)

## 🧠 Strategy contribution summary
- trend_following: avg 69/100 (weight 20)
- relative_strength: avg 42/100 (weight 20)
- mean_reversion _(display-only)_: avg 50/100 (weight 0)
- breakout _(display-only)_: avg 55/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 46/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- HDFCBANK.NS: Disagreement: ['trend_following', 'relative_strength', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- SBIN.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- AXISBANK.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- LT.NS: Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- ITC.NS: Disagreement: ['trend_following', 'volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- HDFCBANK.NS (WATCH, 73.6): Final 73.6/100 -> WATCH [regime RISK_ON]. Top: relative_strength=100, trend_following=90, portfolio_fit=80. Disagreement: ['trend_following', 'relative_strength', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- ICICIBANK.NS (WATCH, 71.1): Final 71.1/100 -> WATCH [regime RISK_ON]. Top: trend_following=96, portfolio_fit=80, news_event_risk=65.
- RELIANCE.NS (WATCH, 70.2): Final 70.2/100 -> WATCH [regime RISK_ON]. Top: trend_following=86, portfolio_fit=80, relative_strength=67.
- BHARTIARTL.NS (WATCH, 68.0): Final 68.0/100 -> WATCH [regime RISK_ON]. Top: trend_following=90, portfolio_fit=80, news_event_risk=65.
- SBIN.NS (NO_ACTION, 62.6): Final 62.6/100 -> NO_ACTION [regime RISK_ON]. Top: trend_following=88, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- AXISBANK.NS (NO_ACTION, 61.8): Final 61.8/100 -> NO_ACTION [regime RISK_ON]. Top: trend_following=86, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- LT.NS (NO_ACTION, 55.8): Final 55.8/100 -> NO_ACTION [regime RISK_ON]. Top: trend_following=80, news_event_risk=65, volatility_risk=43. Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- ITC.NS (HOLD, 55.3): Final 55.3/100 -> HOLD [regime RISK_ON]. Top: volatility_risk=73, trend_following=72, news_event_risk=65. Disagreement: ['trend_following', 'volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 36 · total this month: 144 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2058 exceeds per-trade cap ₹2000.
- Share price ₹4041 exceeds per-trade cap ₹2000.
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