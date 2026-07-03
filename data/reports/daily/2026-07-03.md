# 📄 Paper Trading Report — 2026-07-03 (mid)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (0.07%) — neutral regime.

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
BHARTIARTL.NS(72.4), ICICIBANK.NS(68.7), HDFCBANK.NS(65.5)

## 🚫 Do-not-buy
LT.NS(46.0), TCS.NS(41.2), INFY.NS(40.5)

## 🧠 Strategy contribution summary
- trend_following: avg 63/100 (weight 20)
- relative_strength: avg 46/100 (weight 20)
- mean_reversion _(display-only)_: avg 50/100 (weight 0)
- breakout _(display-only)_: avg 55/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 48/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- ITC.NS: Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- AXISBANK.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- TCS.NS: Disagreement: ['relative_strength'] positive vs ['trend_following', 'volatility_risk', 'portfolio_fit'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- BHARTIARTL.NS (WATCH, 72.4): Final 72.4/100 -> WATCH [regime NEUTRAL]. Top: relative_strength=89, trend_following=86, portfolio_fit=80.
- ICICIBANK.NS (WATCH, 68.7): Final 68.7/100 -> WATCH [regime NEUTRAL]. Top: trend_following=94, portfolio_fit=80, news_event_risk=65.
- HDFCBANK.NS (WATCH, 65.5): Final 65.5/100 -> WATCH [regime NEUTRAL]. Top: trend_following=88, portfolio_fit=80, news_event_risk=65.
- ITC.NS (HOLD, 60.9): Final 60.9/100 -> HOLD [regime NEUTRAL]. Top: trend_following=87, volatility_risk=73, news_event_risk=65. Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- SBIN.NS (NO_ACTION, 56.5): Final 56.5/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=89, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- AXISBANK.NS (NO_ACTION, 54.6): Final 54.6/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=86, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- RELIANCE.NS (NO_ACTION, 53.9): Final 53.9/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=57.
- LT.NS (DO_NOT_BUY, 46.0): Final 46.0/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: news_event_risk=65, trend_following=60, volatility_risk=43.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 24 · total this month: 96 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2096 exceeds per-trade cap ₹2000.
- Share price ₹4034 exceeds per-trade cap ₹2000.
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