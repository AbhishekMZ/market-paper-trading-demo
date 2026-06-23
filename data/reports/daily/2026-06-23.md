# 📄 Paper Trading Report — 2026-06-23 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_ON` — Benchmarks up 1.75% on average — risk-on.

## 💰 Portfolio (fake money)
- Total value: **₹10,000.00** (started ₹10,000.00)
- Cash: ₹8,474.74 · Holdings: ₹1,525.26
- Realized P&L: ₹0.00 · Unrealized: ₹0.00
- Total return: +0.00% · Max drawdown: +0.00%
- Monthly budget: deployed ₹1,525.26 / ₹10,000.00 · buys 1/5
- **Cost-adjusted** net realized: ₹0.00 (est. costs ₹0.00)

## ✅ Top paper-buy candidates
- **ITC.NS** score 85.3 (LOW risk) — Final 85.3/100 -> BUY_SMALL_PAPER [regime RISK_ON]. Top: trend_following=100, volatility_risk=96, news_event_risk=80.

## 🧾 Paper trades executed this run
- BUY ITC.NS x3 @ ₹508.42 → FILLED (Paper BUY filled at limit price.)

## 👀 Watchlist
RELIANCE.NS(76.1)

## 🚫 Do-not-buy
SBIN.NS(44.4), TCS.NS(43.5)

## 🧠 Strategy contribution summary
- trend_following: avg 51/100 (weight 20)
- relative_strength: avg 21/100 (weight 20)
- mean_reversion _(display-only)_: avg 50/100 (weight 0)
- breakout _(display-only)_: avg 52/100 (weight 0)
- news_event_risk: avg 64/100 (weight 15)
- volatility_risk: avg 94/100 (weight 15)
- portfolio_fit: avg 62/100 (weight 10)

## ❗ Strategy conflicts
- RELIANCE.NS: Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- INFY.NS: Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- HDFCBANK.NS: Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- ICICIBANK.NS: Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- BHARTIARTL.NS: Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- AXISBANK.NS: Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- LT.NS: Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- SBIN.NS: Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['trend_following', 'relative_strength'] negative.
- TCS.NS: Disagreement: ['volatility_risk'] positive vs ['trend_following', 'relative_strength', 'portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- RELIANCE.NS (WATCH, 76.1): Final 76.1/100 -> WATCH [regime RISK_ON]. Top: trend_following=100, volatility_risk=96, news_event_risk=65. Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- INFY.NS (NO_ACTION, 64.0): Final 64.0/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, portfolio_fit=80, news_event_risk=65. Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- HDFCBANK.NS (NO_ACTION, 63.0): Final 63.0/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, portfolio_fit=80, news_event_risk=65. Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- ICICIBANK.NS (NO_ACTION, 62.5): Final 62.5/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, portfolio_fit=80, news_event_risk=65. Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- BHARTIARTL.NS (NO_ACTION, 62.0): Final 62.0/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, portfolio_fit=80, news_event_risk=65. Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- AXISBANK.NS (NO_ACTION, 61.5): Final 61.5/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, portfolio_fit=80, news_event_risk=65. Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- LT.NS (NO_ACTION, 57.5): Final 57.5/100 -> NO_ACTION [regime RISK_ON]. Top: volatility_risk=96, news_event_risk=65, trend_following=52. Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- SBIN.NS (DO_NOT_BUY, 44.4): Final 44.4/100 -> DO_NOT_BUY [regime RISK_ON]. Top: volatility_risk=85, portfolio_fit=80, news_event_risk=41. Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['trend_following', 'relative_strength'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 12 · total this month: 12 (no API-key quota)

## 🧪 Data-quality warnings
- No news data available; using a neutral assumption.
- Share price ₹3072 exceeds per-trade cap ₹2000.
- Share price ₹3626 exceeds per-trade cap ₹2000.
- Share price ₹3702 exceeds per-trade cap ₹2000.

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