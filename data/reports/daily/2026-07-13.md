# 📄 Paper Trading Report — 2026-07-13 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (0.08%) — neutral regime.

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
ICICIBANK.NS(69.1)

## 🚫 Do-not-buy
RELIANCE.NS(49.9), AXISBANK.NS(48.0), ITC.NS(44.0), LT.NS(40.3), TCS.NS(38.0)

## 🧠 Strategy contribution summary
- trend_following: avg 45/100 (weight 20)
- relative_strength: avg 51/100 (weight 20)
- mean_reversion _(display-only)_: avg 46/100 (weight 0)
- breakout _(display-only)_: avg 48/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 46/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- HDFCBANK.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- BHARTIARTL.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- INFY.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- RELIANCE.NS: Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- AXISBANK.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- ITC.NS: Disagreement: ['volatility_risk'] positive vs ['trend_following', 'relative_strength', 'portfolio_fit'] negative.
- LT.NS: Disagreement: ['volatility_risk'] positive vs ['trend_following', 'portfolio_fit'] negative.
- TCS.NS: Disagreement: ['relative_strength'] positive vs ['volatility_risk', 'portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- ICICIBANK.NS (WATCH, 69.1): Final 69.1/100 -> WATCH [regime NEUTRAL]. Top: trend_following=94, portfolio_fit=80, news_event_risk=65.
- SBIN.NS (NO_ACTION, 59.4): Final 59.4/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, trend_following=58.
- HDFCBANK.NS (NO_ACTION, 58.8): Final 58.8/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=88, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- BHARTIARTL.NS (NO_ACTION, 56.7): Final 56.7/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, trend_following=73, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- INFY.NS (NO_ACTION, 52.4): Final 52.4/100 -> NO_ACTION [regime NEUTRAL]. Top: relative_strength=100, portfolio_fit=80, news_event_risk=65. Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- RELIANCE.NS (DO_NOT_BUY, 49.9): Final 49.9/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=54. Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- AXISBANK.NS (DO_NOT_BUY, 48.0): Final 48.0/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=57. Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- ITC.NS (DO_NOT_BUY, 44.0): Final 44.0/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: volatility_risk=66, news_event_risk=65, portfolio_fit=35. Disagreement: ['volatility_risk'] positive vs ['trend_following', 'relative_strength', 'portfolio_fit'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 36 · total this month: 324 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2182 exceeds per-trade cap ₹2000.
- Share price ₹3928 exceeds per-trade cap ₹2000.
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