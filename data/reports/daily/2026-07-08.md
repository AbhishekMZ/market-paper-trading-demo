# 📄 Paper Trading Report — 2026-07-08 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `EVENT_RISK` — Index moved 2.51% / volatility 0.82% — elevated event risk. New buys require manual review.

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
None.

## 🚫 Do-not-buy
ITC.NS(45.4), INFY.NS(43.6), LT.NS(41.5), TCS.NS(34.1)

## 🧠 Strategy contribution summary
- trend_following: avg 56/100 (weight 20)
- relative_strength: avg 51/100 (weight 20)
- mean_reversion _(display-only)_: avg 54/100 (weight 0)
- breakout _(display-only)_: avg 48/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 44/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- INFY.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- BHARTIARTL.NS (NO_ACTION, 59.5): Final 59.5/100 -> NO_ACTION [regime EVENT_RISK]. Top: trend_following=81, portfolio_fit=80, news_event_risk=65.
- ICICIBANK.NS (NO_ACTION, 59.3): Final 59.3/100 -> NO_ACTION [regime EVENT_RISK]. Top: trend_following=93, portfolio_fit=80, news_event_risk=65.
- SBIN.NS (NO_ACTION, 57.9): Final 57.9/100 -> NO_ACTION [regime EVENT_RISK]. Top: portfolio_fit=80, trend_following=75, news_event_risk=65.
- HDFCBANK.NS (NO_ACTION, 56.9): Final 56.9/100 -> NO_ACTION [regime EVENT_RISK]. Top: trend_following=88, portfolio_fit=80, news_event_risk=65.
- AXISBANK.NS (NO_ACTION, 54.8): Final 54.8/100 -> NO_ACTION [regime EVENT_RISK]. Top: portfolio_fit=80, trend_following=71, news_event_risk=65.
- RELIANCE.NS (NO_ACTION, 51.0): Final 51.0/100 -> NO_ACTION [regime EVENT_RISK]. Top: portfolio_fit=80, news_event_risk=65, volatility_risk=54.
- ITC.NS (DO_NOT_BUY, 45.4): Final 45.4/100 -> DO_NOT_BUY [regime EVENT_RISK]. Top: news_event_risk=65, volatility_risk=64, trend_following=48.
- INFY.NS (DO_NOT_BUY, 43.6): Final 43.6/100 -> DO_NOT_BUY [regime EVENT_RISK]. Top: relative_strength=97, portfolio_fit=80, news_event_risk=65. Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 36 · total this month: 216 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- Market regime: EVENT_RISK.
- Share price ₹2058 exceeds per-trade cap ₹2000.
- Share price ₹3892 exceeds per-trade cap ₹2000.
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