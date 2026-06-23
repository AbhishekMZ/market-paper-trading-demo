# 📄 Paper Trading Report — 2026-06-23 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (0.02%) — neutral regime.

## 💰 Portfolio (fake money)
- Total value: **₹10,000.00** (started ₹10,000.00)
- Cash: ₹10,000.00 · Holdings: ₹0.00
- Realized P&L: ₹0.00 · Unrealized: ₹0.00
- Total return: +0.00% · Max drawdown: +0.00%
- Monthly budget: deployed ₹0.00 / ₹10,000.00 · buys 0/5
- **Cost-adjusted** net realized: ₹0.00 (est. costs ₹0.00)

## ✅ Top paper-buy candidates
- None this checkpoint.

## 👀 Watchlist
ICICIBANK.NS(67.8)

## 🚫 Do-not-buy
ITC.NS(48.9), RELIANCE.NS(46.7), INFY.NS(25.1), TCS.NS(22.8)

## 🧠 Strategy contribution summary
- trend_following: avg 48/100 (weight 20)
- relative_strength: avg 44/100 (weight 20)
- mean_reversion _(display-only)_: avg 47/100 (weight 0)
- breakout _(display-only)_: avg 59/100 (weight 0)
- news_event_risk: avg 56/100 (weight 15)
- volatility_risk: avg 43/100 (weight 15)
- portfolio_fit: avg 68/100 (weight 10)

## ❗ Strategy conflicts
- LT.NS: Disagreement: ['trend_following', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- ITC.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- RELIANCE.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- ICICIBANK.NS (WATCH, 67.8): Final 67.8/100 -> WATCH [regime NEUTRAL]. Top: trend_following=90, portfolio_fit=80, relative_strength=67.
- SBIN.NS (NO_ACTION, 64.8): Final 64.8/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=89, portfolio_fit=80, volatility_risk=67.
- BHARTIARTL.NS (NO_ACTION, 64.0): Final 64.0/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=75, trend_following=67.
- AXISBANK.NS (NO_ACTION, 60.7): Final 60.7/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, trend_following=79, relative_strength=58.
- LT.NS (NO_ACTION, 58.1): Final 58.1/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=84, news_event_risk=70, relative_strength=57. Disagreement: ['trend_following', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- HDFCBANK.NS (NO_ACTION, 52.3): Final 52.3/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=53, relative_strength=50.
- ITC.NS (DO_NOT_BUY, 48.9): Final 48.9/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, relative_strength=54. Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- RELIANCE.NS (DO_NOT_BUY, 46.7): Final 46.7/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: portfolio_fit=80, volatility_risk=56, relative_strength=49. Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 12 · total this month: 12 (no API-key quota)

## 🧪 Data-quality warnings
- Share price ₹2086 exceeds per-trade cap ₹2000.
- Share price ₹4216 exceeds per-trade cap ₹2000.

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