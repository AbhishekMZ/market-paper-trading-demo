# 📄 Paper Trading Report — 2026-07-08 (mid)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_OFF` — Benchmarks down -0.93% on average — risk-off. New buys blocked.

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
ITC.NS(49.1), LT.NS(47.7), INFY.NS(40.8), TCS.NS(35.5)

## 🧠 Strategy contribution summary
- trend_following: avg 63/100 (weight 20)
- relative_strength: avg 50/100 (weight 20)
- mean_reversion _(display-only)_: avg 56/100 (weight 0)
- breakout _(display-only)_: avg 50/100 (weight 0)
- news_event_risk: avg 65/100 (weight 15)
- volatility_risk: avg 46/100 (weight 15)
- portfolio_fit: avg 64/100 (weight 10)

## ❗ Strategy conflicts
- BHARTIARTL.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- ITC.NS: Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- INFY.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- SBIN.NS (NO_ACTION, 63.0): [DATA DATA_ANOMALY] Final 63.0/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=88, portfolio_fit=80, news_event_risk=65.
- HDFCBANK.NS (NO_ACTION, 61.0): [DATA DATA_ANOMALY] Final 61.0/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=88, portfolio_fit=80, news_event_risk=65.
- AXISBANK.NS (NO_ACTION, 60.2): [DATA DATA_ANOMALY] Final 60.2/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=84, portfolio_fit=80, news_event_risk=65.
- ICICIBANK.NS (NO_ACTION, 59.6): [DATA DATA_ANOMALY] Final 59.6/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=93, portfolio_fit=80, news_event_risk=65.
- BHARTIARTL.NS (NO_ACTION, 55.3): [DATA DATA_ANOMALY] Final 55.3/100 -> NO_ACTION [regime RISK_OFF]. Top: trend_following=82, portfolio_fit=80, news_event_risk=65. Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- RELIANCE.NS (NO_ACTION, 53.2): [DATA DATA_ANOMALY] Final 53.2/100 -> NO_ACTION [regime RISK_OFF]. Top: portfolio_fit=80, news_event_risk=65, trend_following=62.
- ITC.NS (DO_NOT_BUY, 49.1): [DATA DATA_ANOMALY] Final 49.1/100 -> DO_NOT_BUY [regime RISK_OFF]. Top: volatility_risk=70, news_event_risk=65, trend_following=58. Disagreement: ['volatility_risk'] positive vs ['relative_strength', 'portfolio_fit'] negative.
- LT.NS (DO_NOT_BUY, 47.7): [DATA DATA_ANOMALY] Final 47.7/100 -> DO_NOT_BUY [regime RISK_OFF]. Top: news_event_risk=65, trend_following=60, relative_strength=52.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 24 · total this month: 204 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- DataQuality:DATA_ANOMALY
- Market regime: RISK_OFF.
- Share price ₹2077 exceeds per-trade cap ₹2000.
- Share price ₹3956 exceeds per-trade cap ₹2000.
- price source changed today: fallback -> history.close.
- 11 data-quality incident(s) this run — see Data Health.

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