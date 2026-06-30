# 📄 Paper Trading Report — 2026-06-30 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (-0.33%) — neutral regime.

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
HDFCBANK.NS(65.1)

## 🚫 Do-not-buy
INFY.NS(28.7), TCS.NS(22.8)

## 🧠 Strategy contribution summary
- trend_following: avg 59/100 (weight 20)
- relative_strength: avg 36/100 (weight 20)
- mean_reversion _(display-only)_: avg 48/100 (weight 0)
- breakout _(display-only)_: avg 52/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 44/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- ITC.NS: Disagreement: ['trend_following', 'volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- LT.NS: Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- RELIANCE.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- HDFCBANK.NS (WATCH, 65.1): Final 65.1/100 -> WATCH [regime NEUTRAL]. Top: trend_following=90, portfolio_fit=80, news_event_risk=65.
- BHARTIARTL.NS (NO_ACTION, 64.8): Final 64.8/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, relative_strength=73, news_event_risk=65.
- SBIN.NS (NO_ACTION, 63.3): Final 63.3/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=90, portfolio_fit=80, news_event_risk=65.
- ICICIBANK.NS (NO_ACTION, 63.2): Final 63.2/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=93, portfolio_fit=80, news_event_risk=65.
- AXISBANK.NS (NO_ACTION, 61.8): Final 61.8/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=87, portfolio_fit=80, news_event_risk=65.
- ITC.NS (HOLD, 52.8): Final 52.8/100 -> HOLD [regime NEUTRAL]. Top: trend_following=67, volatility_risk=65, news_event_risk=65. Disagreement: ['trend_following', 'volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- LT.NS (NO_ACTION, 52.4): Final 52.4/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=71, news_event_risk=65, relative_strength=45. Disagreement: ['trend_following'] positive vs ['portfolio_fit'] negative.
- RELIANCE.NS (NO_ACTION, 51.3): Final 51.3/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=57. Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 36 · total this month: 336 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2032 exceeds per-trade cap ₹2000.
- Share price ₹4143 exceeds per-trade cap ₹2000.
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