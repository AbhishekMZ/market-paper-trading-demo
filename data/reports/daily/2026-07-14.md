# 📄 Paper Trading Report — 2026-07-14 (mid)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_OFF` — Benchmarks down -0.82% on average — risk-off. New buys blocked.

## 💰 Portfolio (fake money)
- Total value: **INR10,091.50** (started INR10,000.00)
- Cash: INR8,474.74 · Holdings: INR1,616.76
- Realized P&L: INR0.00 · Unrealized: INR91.50
- Total return: +0.91% · Max drawdown: +0.00%
- Monthly budget: deployed INR0.00 / INR100,000.00 · buys 0/250
- **Cost-adjusted** net realized: INR0.00 (est. costs INR0.00)

## ✅ Top paper-buy candidates
- None this checkpoint.

## 👀 Watchlist
BHARTIARTL.NS(71.2), SUNPHARMA.NS(68.6), TECHM.NS(66.0), CIPLA.NS(65.4), ICICIBANK.NS(62.1), TITAN.NS(60.9)

## 🚫 Do-not-buy
HINDUNILVR.NS(49.9), ASIANPAINT.NS(49.1), JSWSTEEL.NS(47.5), WIPRO.NS(46.3), SBIN.NS(44.7), AXISBANK.NS(43.2), HCLTECH.NS(42.5), ITC.NS(40.2), ULTRACEMCO.NS(39.7), LT.NS(36.4), INFY.NS(35.9), TATAMOTORS.NS(34.4), KOTAKBANK.NS(34.0), MARUTI.NS(29.4)

## 🧠 Strategy contribution summary
- trend_following: avg 48/100 (weight 18)
- relative_strength: avg 50/100 (weight 20)
- mean_reversion: avg 47/100 (weight 4)
- breakout: avg 51/100 (weight 8)
- news_event_risk: avg 65/100 (weight 14)
- volatility_risk: avg 46/100 (weight 12)
- portfolio_fit: avg 75/100 (weight 8)

## ❗ Strategy conflicts
- TECHM.NS: Disagreement: ['trend_following', 'relative_strength', 'breakout', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- BAJFINANCE.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- COALINDIA.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following'] negative.
- TCS.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- NESTLEIND.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- TATASTEEL.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following'] negative.
- DRREDDY.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- BRITANNIA.NS: Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- BAJAJFINSV.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- HINDUNILVR.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- ASIANPAINT.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- JSWSTEEL.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- WIPRO.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- SBIN.NS: Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- AXISBANK.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- HCLTECH.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength', 'volatility_risk'] negative.
- ITC.NS: Disagreement: ['volatility_risk'] positive vs ['trend_following', 'portfolio_fit'] negative.
- LT.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- KOTAKBANK.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength'] negative.

## 🤔 Why no trade (selected)
- BHARTIARTL.NS (WATCH, 71.2): Final 71.2/100 -> WATCH [regime RISK_OFF]. Top: relative_strength=100, trend_following=89, portfolio_fit=80. RISK_OFF regime -> new buys blocked; downgraded to WATCH.
- SUNPHARMA.NS (WATCH, 68.6): Final 68.6/100 -> WATCH [regime RISK_OFF]. Top: trend_following=91, portfolio_fit=80, relative_strength=77.
- TECHM.NS (WATCH, 66.0): Final 66.0/100 -> WATCH [regime RISK_OFF]. Top: relative_strength=100, trend_following=84, portfolio_fit=80. Disagreement: ['trend_following', 'relative_strength', 'breakout', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- CIPLA.NS (WATCH, 65.4): Final 65.4/100 -> WATCH [regime RISK_OFF]. Top: trend_following=88, relative_strength=84, portfolio_fit=80.
- ICICIBANK.NS (WATCH, 62.1): Final 62.1/100 -> WATCH [regime RISK_OFF]. Top: trend_following=93, portfolio_fit=80, news_event_risk=65.
- TITAN.NS (WATCH, 60.9): Final 60.9/100 -> WATCH [regime RISK_OFF]. Top: trend_following=87, portfolio_fit=80, breakout=70.
- ONGC.NS (NO_ACTION, 57.7): Final 57.7/100 -> NO_ACTION [regime RISK_OFF]. Top: portfolio_fit=80, breakout=70, news_event_risk=65.
- ADANIPORTS.NS (NO_ACTION, 56.5): Final 56.5/100 -> NO_ACTION [regime RISK_OFF]. Top: portfolio_fit=80, relative_strength=74, news_event_risk=65.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 72 · total this month: 396 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- DataQuality:DATA_INSUFFICIENT
- Market regime: RISK_OFF.
- Share price ₹11490 exceeds per-trade cap ₹10000.
- Share price ₹13530 exceeds per-trade cap ₹10000.
- Sparse price series (data gap); volatility under-measured.
- insufficient_data
- missing_change_pct
- missing_graph
- no current price.
- 2 data-quality incident(s) this run — see Data Health.

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