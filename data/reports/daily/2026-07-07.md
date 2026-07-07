# 📄 Paper Trading Report — 2026-07-07 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (-0.14%) — neutral regime.

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
BHARTIARTL.NS(66.2), SBIN.NS(66.1), AXISBANK.NS(65.5)

## 🚫 Do-not-buy
INFY.NS(48.7), LT.NS(47.5)

## 🧠 Strategy contribution summary
- trend_following: avg 69/100 (weight 20)
- relative_strength: avg 56/100 (weight 20)
- mean_reversion _(display-only)_: avg 51/100 (weight 0)
- breakout _(display-only)_: avg 55/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 47/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- ICICIBANK.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- ITC.NS: Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- RELIANCE.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- TCS.NS: Disagreement: ['relative_strength'] positive vs ['trend_following', 'volatility_risk', 'portfolio_fit'] negative.
- INFY.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- LT.NS: Disagreement: ['trend_following'] positive vs ['relative_strength', 'portfolio_fit'] negative.

## 🤔 Why no trade (selected)
- BHARTIARTL.NS (WATCH, 66.2): Final 66.2/100 -> WATCH [regime NEUTRAL]. Top: trend_following=90, portfolio_fit=80, news_event_risk=65.
- SBIN.NS (WATCH, 66.1): Final 66.1/100 -> WATCH [regime NEUTRAL]. Top: trend_following=89, portfolio_fit=80, news_event_risk=65.
- AXISBANK.NS (WATCH, 65.5): Final 65.5/100 -> WATCH [regime NEUTRAL]. Top: trend_following=87, portfolio_fit=80, news_event_risk=65.
- HDFCBANK.NS (NO_ACTION, 63.5): Final 63.5/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=89, portfolio_fit=80, news_event_risk=65.
- ICICIBANK.NS (NO_ACTION, 62.9): Final 62.9/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=94, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- ITC.NS (HOLD, 61.6): Final 61.6/100 -> HOLD [regime NEUTRAL]. Top: trend_following=74, volatility_risk=74, news_event_risk=65. Disagreement: ['trend_following', 'volatility_risk'] positive vs ['portfolio_fit'] negative.
- RELIANCE.NS (NO_ACTION, 58.6): Final 58.6/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, trend_following=76, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- TCS.NS (NO_ACTION, 50.4): Final 50.4/100 -> NO_ACTION [regime NEUTRAL]. Top: relative_strength=100, news_event_risk=65, volatility_risk=23. Disagreement: ['relative_strength'] positive vs ['trend_following', 'volatility_risk', 'portfolio_fit'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 36 · total this month: 180 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2096 exceeds per-trade cap ₹2000.
- Share price ₹3992 exceeds per-trade cap ₹2000.
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