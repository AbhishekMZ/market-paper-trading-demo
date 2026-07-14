# 📄 Paper Trading Report — 2026-07-14 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `RISK_OFF` — Benchmarks down -0.90% on average — risk-off. New buys blocked.

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
SUNPHARMA.NS(71.6), BHARTIARTL.NS(71.2), CIPLA.NS(64.4), ICICIBANK.NS(63.5), TITAN.NS(61.3), ONGC.NS(61.0), NESTLEIND.NS(60.1)

## 🚫 Do-not-buy
TATASTEEL.NS(49.8), TECHM.NS(49.3), HINDUNILVR.NS(48.2), AXISBANK.NS(48.0), ULTRACEMCO.NS(47.0), ASIANPAINT.NS(46.6), WIPRO.NS(45.9), SBIN.NS(43.0), HCLTECH.NS(40.2), ITC.NS(37.8), INFY.NS(37.4), LT.NS(37.2), KOTAKBANK.NS(36.4), TATAMOTORS.NS(34.4), MARUTI.NS(34.2)

## 🧠 Strategy contribution summary
- trend_following: avg 46/100 (weight 18)
- relative_strength: avg 54/100 (weight 20)
- mean_reversion: avg 46/100 (weight 4)
- breakout: avg 51/100 (weight 8)
- news_event_risk: avg 65/100 (weight 14)
- volatility_risk: avg 47/100 (weight 12)
- portfolio_fit: avg 75/100 (weight 8)

## ❗ Strategy conflicts
- TCS.NS: Disagreement: ['relative_strength', 'breakout', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- BAJFINANCE.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- JSWSTEEL.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following'] negative.
- DRREDDY.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- BAJAJFINSV.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- RELIANCE.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- COALINDIA.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following'] negative.
- TATASTEEL.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following'] negative.
- TECHM.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength', 'volatility_risk'] negative.
- HINDUNILVR.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- AXISBANK.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- ASIANPAINT.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- WIPRO.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- SBIN.NS: Disagreement: ['portfolio_fit'] positive vs ['relative_strength'] negative.
- HCLTECH.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength', 'mean_reversion', 'volatility_risk'] negative.
- ITC.NS: Disagreement: ['volatility_risk'] positive vs ['trend_following', 'relative_strength', 'portfolio_fit'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- LT.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength'] negative.
- KOTAKBANK.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'relative_strength'] negative.

## 🤔 Why no trade (selected)
- SUNPHARMA.NS (WATCH, 71.6): Final 71.6/100 -> WATCH [regime RISK_OFF]. Top: relative_strength=94, trend_following=90, portfolio_fit=80. RISK_OFF regime -> new buys blocked; downgraded to WATCH.
- BHARTIARTL.NS (WATCH, 71.2): Final 71.2/100 -> WATCH [regime RISK_OFF]. Top: relative_strength=100, trend_following=89, portfolio_fit=80. RISK_OFF regime -> new buys blocked; downgraded to WATCH.
- CIPLA.NS (WATCH, 64.4): Final 64.4/100 -> WATCH [regime RISK_OFF]. Top: relative_strength=86, portfolio_fit=80, trend_following=79.
- ICICIBANK.NS (WATCH, 63.5): Final 63.5/100 -> WATCH [regime RISK_OFF]. Top: trend_following=93, portfolio_fit=80, news_event_risk=65.
- TITAN.NS (WATCH, 61.3): Final 61.3/100 -> WATCH [regime RISK_OFF]. Top: trend_following=87, portfolio_fit=80, breakout=70.
- ONGC.NS (WATCH, 61.0): Final 61.0/100 -> WATCH [regime RISK_OFF]. Top: portfolio_fit=80, relative_strength=71, breakout=70.
- NESTLEIND.NS (WATCH, 60.1): Final 60.1/100 -> WATCH [regime RISK_OFF]. Top: portfolio_fit=80, trend_following=76, relative_strength=67.
- ADANIPORTS.NS (NO_ACTION, 58.4): Final 58.4/100 -> NO_ACTION [regime RISK_OFF]. Top: relative_strength=82, portfolio_fit=80, news_event_risk=65.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 108 · total this month: 432 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- DataQuality:DATA_INSUFFICIENT
- Market regime: RISK_OFF.
- Share price ₹11496 exceeds per-trade cap ₹10000.
- Share price ₹13489 exceeds per-trade cap ₹10000.
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