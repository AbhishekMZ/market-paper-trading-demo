# 📄 Paper Trading Report — 2026-06-29 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (-0.61%) — neutral regime.

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
ICICIBANK.NS(67.9), HDFCBANK.NS(67.7)

## 🚫 Do-not-buy
RELIANCE.NS(48.8), LT.NS(47.0), INFY.NS(38.9), TCS.NS(35.8)

## 🧠 Strategy contribution summary
- trend_following: avg 55/100 (weight 20)
- relative_strength: avg 49/100 (weight 20)
- mean_reversion _(display-only)_: avg 48/100 (weight 0)
- breakout _(display-only)_: avg 52/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 43/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- AXISBANK.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- ITC.NS: Disagreement: ['relative_strength'] positive vs ['portfolio_fit'] negative.
- RELIANCE.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- TCS.NS: Disagreement: ['relative_strength'] positive vs ['trend_following', 'volatility_risk', 'portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- ICICIBANK.NS (WATCH, 67.9): Final 67.9/100 -> WATCH [regime NEUTRAL]. Top: trend_following=92, portfolio_fit=80, news_event_risk=65.
- HDFCBANK.NS (WATCH, 67.7): Final 67.7/100 -> WATCH [regime NEUTRAL]. Top: trend_following=90, portfolio_fit=80, relative_strength=70.
- SBIN.NS (NO_ACTION, 63.6): Final 63.6/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=90, portfolio_fit=80, news_event_risk=65.
- AXISBANK.NS (NO_ACTION, 58.7): Final 58.7/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=86, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- ITC.NS (HOLD, 57.8): Final 57.8/100 -> HOLD [regime NEUTRAL]. Top: relative_strength=67, news_event_risk=65, volatility_risk=59. Disagreement: ['relative_strength'] positive vs ['portfolio_fit'] negative.
- BHARTIARTL.NS (NO_ACTION, 56.7): Final 56.7/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=58.
- RELIANCE.NS (DO_NOT_BUY, 48.8): Final 48.8/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=56. Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength'] negative.
- LT.NS (DO_NOT_BUY, 47.0): Final 47.0/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: news_event_risk=65, trend_following=61, volatility_risk=39.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 36 · total this month: 300 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2098 exceeds per-trade cap ₹2000.
- Share price ₹4165 exceeds per-trade cap ₹2000.
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