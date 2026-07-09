# 📄 Paper Trading Report — 2026-07-09 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (0.56%) — neutral regime.

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
BHARTIARTL.NS(74.5), HDFCBANK.NS(65.3)

## 🚫 Do-not-buy
AXISBANK.NS(49.2), LT.NS(44.0), TCS.NS(32.2), INFY.NS(28.7)

## 🧠 Strategy contribution summary
- trend_following: avg 52/100 (weight 20)
- relative_strength: avg 44/100 (weight 20)
- mean_reversion _(display-only)_: avg 50/100 (weight 0)
- breakout _(display-only)_: avg 50/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 44/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- AXISBANK.NS: Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- BHARTIARTL.NS (WATCH, 74.5): Final 74.5/100 -> WATCH [regime NEUTRAL]. Top: relative_strength=98, trend_following=90, portfolio_fit=80.
- HDFCBANK.NS (WATCH, 65.3): Final 65.3/100 -> WATCH [regime NEUTRAL]. Top: trend_following=89, portfolio_fit=80, news_event_risk=65.
- ICICIBANK.NS (NO_ACTION, 63.5): Final 63.5/100 -> NO_ACTION [regime NEUTRAL]. Top: trend_following=92, portfolio_fit=80, news_event_risk=65.
- SBIN.NS (NO_ACTION, 59.9): Final 59.9/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, trend_following=60.
- RELIANCE.NS (NO_ACTION, 56.8): Final 56.8/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=55.
- ITC.NS (HOLD, 54.2): Final 54.2/100 -> HOLD [regime NEUTRAL]. Top: news_event_risk=65, volatility_risk=64, relative_strength=52.
- AXISBANK.NS (DO_NOT_BUY, 49.2): Final 49.2/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=52. Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- LT.NS (DO_NOT_BUY, 44.0): Final 44.0/100 -> DO_NOT_BUY [regime NEUTRAL]. Top: news_event_risk=65, volatility_risk=40, trend_following=38.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 24 · total this month: 240 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Share price ₹2046 exceeds per-trade cap ₹2000.
- Share price ₹3885 exceeds per-trade cap ₹2000.
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