# 📄 Paper Trading Report — 2026-06-23 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_ON` — Benchmarks up 1.75% on average — risk-on.

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
ITC.NS(78.8), RELIANCE.NS(75.6)

## 🚫 Do-not-buy
TCS.NS(43.0), SBIN.NS(37.9)

## 🧠 Strategy contribution summary
- trend_following: avg 51/100 (weight 20)
- relative_strength: avg 21/100 (weight 20)
- mean_reversion _(display-only)_: avg 50/100 (weight 0)
- breakout _(display-only)_: avg 52/100 (weight 0)
- news_event_risk: avg 64/100 (weight 15)
- volatility_risk: avg 94/100 (weight 15)
- portfolio_fit: avg 15/100 (weight 10)

## ❗ Strategy conflicts
- ITC.NS: Disagreement: ['trend_following', 'relative_strength', 'news_event_risk', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- RELIANCE.NS: Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- INFY.NS: Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- LT.NS: Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- HDFCBANK.NS: Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- ICICIBANK.NS: Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- BHARTIARTL.NS: Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- AXISBANK.NS: Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- TCS.NS: Disagreement: ['volatility_risk'] positive vs ['trend_following', 'relative_strength', 'portfolio_fit'] negative.
- SBIN.NS: Disagreement: ['volatility_risk'] positive vs ['trend_following', 'relative_strength', 'portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- ITC.NS (WATCH, 78.8): Final 78.8/100 -> WATCH [regime RISK_ON]. Top: trend_following=100, volatility_risk=96, news_event_risk=80. Disagreement: ['trend_following', 'relative_strength', 'news_event_risk', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- RELIANCE.NS (WATCH, 75.6): Final 75.6/100 -> WATCH [regime RISK_ON]. Top: trend_following=100, volatility_risk=96, news_event_risk=65. Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- INFY.NS (NO_ACTION, 57.5): Final 57.5/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, news_event_risk=65, trend_following=52. Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- LT.NS (NO_ACTION, 57.0): Final 57.0/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, news_event_risk=65, trend_following=52. Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- HDFCBANK.NS (NO_ACTION, 56.5): Final 56.5/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, news_event_risk=65, trend_following=52. Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- ICICIBANK.NS (NO_ACTION, 56.0): Final 56.0/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, news_event_risk=65, trend_following=52. Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- BHARTIARTL.NS (NO_ACTION, 55.5): Final 55.5/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, news_event_risk=65, trend_following=52. Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- AXISBANK.NS (NO_ACTION, 55.0): Final 55.0/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, news_event_risk=65, trend_following=52. Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 72 · total this month: 72 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Daily buy limit reached.
- No news data available; using a neutral assumption.
- Share price ₹3256 exceeds per-trade cap ₹2000.
- Share price ₹3517 exceeds per-trade cap ₹2000.
- Share price ₹3644 exceeds per-trade cap ₹2000.

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