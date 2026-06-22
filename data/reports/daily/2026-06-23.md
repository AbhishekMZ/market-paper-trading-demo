# 📄 Paper Trading Report — 2026-06-23 (manual)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (-0.56%) — neutral regime.

## 💰 Portfolio (fake money)
- Total value: **₹9,352.24** (started ₹10,000.00)
- Cash: ₹8,474.74 · Holdings: ₹877.50
- Realized P&L: ₹0.00 · Unrealized: ₹-647.76
- Total return: -6.48% · Max drawdown: -6.48%
- Monthly budget: deployed ₹1,525.26 / ₹10,000.00 · buys 1/5
- **Cost-adjusted** net realized: ₹0.00 (est. costs ₹0.00)

## ✅ Top paper-buy candidates
- None this checkpoint.

## ⚠️ Positions under review (no auto-sell)
- ITC.NS: -42.47% → EXIT_REVIEW (ITC.NS at -42.47% breaches the -15% review level. No automatic sell — flagged for manual review.)

## 👀 Watchlist
BHARTIARTL.NS(65.1)

## 🚫 Do-not-buy
ITC.NS(48.3), HDFCBANK.NS(39.1), RELIANCE.NS(35.9), TCS.NS(22.2), INFY.NS(3.6)

## 🧠 Strategy contribution summary
- trend_following: avg 50/100 (weight 20)
- relative_strength: avg 48/100 (weight 20)
- mean_reversion _(display-only)_: avg 46/100 (weight 0)
- breakout _(display-only)_: avg 59/100 (weight 0)
- news_event_risk: avg 56/100 (weight 15)
- volatility_risk: avg 41/100 (weight 15)
- portfolio_fit: avg 15/100 (weight 10)

## ❗ Strategy conflicts
- BHARTIARTL.NS: Disagreement: ['relative_strength', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- ICICIBANK.NS: Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- LT.NS: Disagreement: ['trend_following', 'relative_strength', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS: Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- AXISBANK.NS: Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- ITC.NS: Disagreement: ['relative_strength'] positive vs ['trend_following', 'portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- BHARTIARTL.NS (WATCH, 65.1): Final 65.1/100 -> WATCH [regime NEUTRAL]. Top: relative_strength=100, news_event_risk=75, trend_following=62. Disagreement: ['relative_strength', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- ICICIBANK.NS (NO_ACTION, 62.0): Final 62.0/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=90, relative_strength=74, news_event_risk=58. Disagreement: ['trend_following', 'relative_strength'] positive vs ['portfolio_fit'] negative.
- LT.NS (NO_ACTION, 62.0): Final 62.0/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=90, relative_strength=78, news_event_risk=70. Disagreement: ['trend_following', 'relative_strength', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS (NO_ACTION, 57.1): Final 57.1/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=88, volatility_risk=63, news_event_risk=53. Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- AXISBANK.NS (NO_ACTION, 56.0): Final 56.0/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=86, relative_strength=62, volatility_risk=51. Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- ITC.NS (DO_NOT_BUY, 48.3): Final 48.3/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: relative_strength=78, news_event_risk=65, volatility_risk=48. Disagreement: ['relative_strength'] positive vs ['trend_following', 'portfolio_fit'] negative.
- HDFCBANK.NS (DO_NOT_BUY, 39.1): Final 39.1/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: trend_following=58, news_event_risk=53, volatility_risk=39.
- RELIANCE.NS (DO_NOT_BUY, 35.9): Final 35.9/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: volatility_risk=55, news_event_risk=41, relative_strength=31.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 24 · total this month: 24 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Daily buy limit reached.
- Share price ₹2125 exceeds per-trade cap ₹2000.
- Share price ₹4209 exceeds per-trade cap ₹2000.

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