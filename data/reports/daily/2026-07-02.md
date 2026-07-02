# 📄 Paper Trading Report — 2026-07-02 (mid)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (0.21%) — neutral regime.

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
ICICIBANK.NS(70.9)

## 🚫 Do-not-buy
TCS.NS(42.8), LT.NS(38.0), INFY.NS(33.7)

## 🧠 Strategy contribution summary
- trend_following: avg 58/100 (weight 20)
- relative_strength: avg 47/100 (weight 20)
- mean_reversion _(display-only)_: avg 50/100 (weight 0)
- breakout _(display-only)_: avg 54/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 45/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- AXISBANK.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- BHARTIARTL.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- ITC.NS: Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- RELIANCE.NS: Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- TCS.NS: Disagreement: ['relative_strength'] positive vs ['trend_following', 'volatility_risk', 'portfolio_fit'] negative.
- INFY.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- ICICIBANK.NS (WATCH, 70.9): Final 70.9/100 -> WATCH [regime NEUTRAL]. Top: trend_following=94, portfolio_fit=80, relative_strength=71.
- SBIN.NS (NO_ACTION, 64.4): Final 64.4/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=90, portfolio_fit=80, news_event_risk=65.
- HDFCBANK.NS (NO_ACTION, 60.9): Final 60.9/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=88, portfolio_fit=80, news_event_risk=65.
- AXISBANK.NS (NO_ACTION, 59.4): Final 59.4/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=88, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- BHARTIARTL.NS (NO_ACTION, 57.3): Final 57.3/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, trend_following=68, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- ITC.NS (HOLD, 54.0): Final 54.0/100 -> HOLD [regime NEUTRAL]. Top: volatility_risk=66, news_event_risk=65, trend_following=65. Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- RELIANCE.NS (NO_ACTION, 50.4): Final 50.4/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=57. Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- TCS.NS (DO_NOT_BUY, 42.8): Final 42.8/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: relative_strength=100, news_event_risk=65, portfolio_fit=20. Disagreement: ['relative_strength'] positive vs ['trend_following', 'volatility_risk', 'portfolio_fit'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 24 · total this month: 60 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2064 exceeds per-trade cap ₹2000.
- Share price ₹4017 exceeds per-trade cap ₹2000.
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