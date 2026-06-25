# 📄 Paper Trading Report — 2026-06-25 (mid)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (0.31%) — neutral regime.

## 💰 Portfolio (fake money)
- Total value: **₹10,091.50** (started ₹10,000.00)
- Cash: ₹8,474.74 · Holdings: ₹1,616.76
- Realized P&L: ₹0.00 · Unrealized: ₹91.50
- Total return: +0.91% · Max drawdown: +0.00%
- Monthly budget: deployed ₹1,525.26 / ₹10,000.00 · buys 1/100
- **Cost-adjusted** net realized: ₹0.00 (est. costs ₹0.00)

## ✅ Top paper-buy candidates
- None this checkpoint.

## 👀 Watchlist
SBIN.NS(69.2), ICICIBANK.NS(66.1)

## 🚫 Do-not-buy
RELIANCE.NS(46.4), ITC.NS(41.9), TCS.NS(32.1), INFY.NS(30.8)

## 🧠 Strategy contribution summary
- trend_following: avg 46/100 (weight 20)
- relative_strength: avg 47/100 (weight 20)
- mean_reversion _(display-only)_: avg 46/100 (weight 0)
- breakout _(display-only)_: avg 59/100 (weight 0)
- news_event_risk: avg 57/100 (weight 15)
- volatility_risk: avg 42/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- LT.NS: Disagreement: ['trend_following', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- AXISBANK.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- BHARTIARTL.NS: Disagreement: ['news_event_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- RELIANCE.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- SBIN.NS (WATCH, 69.2): Final 69.2/100 -> WATCH [regime NEUTRAL]. Top: trend_following=88, portfolio_fit=80, relative_strength=72.
- ICICIBANK.NS (WATCH, 66.1): Final 66.1/100 -> WATCH [regime NEUTRAL]. Top: trend_following=90, portfolio_fit=80, relative_strength=66.
- LT.NS (NO_ACTION, 60.1): Final 60.1/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=86, news_event_risk=70, relative_strength=64. Disagreement: ['trend_following', 'news_event_risk'] positive vs ['portfolio_fit'] negative.
- AXISBANK.NS (NO_ACTION, 56.4): Final 56.4/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=87, portfolio_fit=80, volatility_risk=55. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- HDFCBANK.NS (NO_ACTION, 55.9): Final 55.9/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, relative_strength=57, trend_following=56.
- BHARTIARTL.NS (NO_ACTION, 50.2): Final 50.2/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=75, volatility_risk=59. Disagreement: ['news_event_risk', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- RELIANCE.NS (DO_NOT_BUY, 46.4): Final 46.4/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: portfolio_fit=80, volatility_risk=56, relative_strength=51. Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- ITC.NS (DO_NOT_BUY, 41.9): Final 41.9/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: news_event_risk=65, volatility_risk=51, relative_strength=44.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 48 · total this month: 204 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2115 exceeds per-trade cap ₹2000.
- Share price ₹4223 exceeds per-trade cap ₹2000.
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