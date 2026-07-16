# 📄 Paper Trading Report — 2026-07-16 (close)

> **PAPER TRADING ONLY — fake money. Live trading is DISABLED.**

**Market regime:** `NEUTRAL` — Benchmarks roughly flat (-0.16%) — neutral regime.

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
BAJFINANCE.NS(72.1), TITAN.NS(69.7), ICICIBANK.NS(66.8), SUNPHARMA.NS(66.0), TECHM.NS(62.5), BHARTIARTL.NS(61.5), HCLTECH.NS(60.2)

## 🚫 Do-not-buy
COALINDIA.NS(47.5), TATASTEEL.NS(46.6), LT.NS(46.3), AXISBANK.NS(46.2), NTPC.NS(46.1), HINDUNILVR.NS(45.8), JSWSTEEL.NS(45.4), DRREDDY.NS(42.9), KOTAKBANK.NS(42.8), INFY.NS(42.6), TATAMOTORS.NS(39.5)

## 🧠 Strategy contribution summary
- trend_following: avg 41/100 (weight 18)
- relative_strength: avg 55/100 (weight 20)
- mean_reversion: avg 46/100 (weight 4)
- breakout: avg 53/100 (weight 8)
- news_event_risk: avg 65/100 (weight 14)
- volatility_risk: avg 48/100 (weight 12)
- portfolio_fit: avg 75/100 (weight 8)

## ❗ Strategy conflicts
- TECHM.NS: Disagreement: ['trend_following', 'relative_strength', 'breakout', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- HCLTECH.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- WIPRO.NS: Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['trend_following'] negative.
- MARUTI.NS: Disagreement: ['relative_strength'] positive vs ['volatility_risk', 'portfolio_fit'] negative.
- ULTRACEMCO.NS: Disagreement: ['trend_following', 'breakout'] positive vs ['portfolio_fit'] negative.
- TCS.NS: Disagreement: ['breakout', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- HDFCBANK.NS: Disagreement: ['trend_following', 'portfolio_fit'] positive vs ['relative_strength'] negative.
- POWERGRID.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- RELIANCE.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- ASIANPAINT.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- ITC.NS: Disagreement: ['relative_strength', 'volatility_risk'] positive vs ['trend_following', 'portfolio_fit'] negative.
- COALINDIA.NS: Disagreement: ['volatility_risk', 'portfolio_fit'] positive vs ['trend_following'] negative.
- TATASTEEL.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- LT.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- AXISBANK.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- NTPC.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- HINDUNILVR.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- JSWSTEEL.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- DRREDDY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.
- KOTAKBANK.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following'] negative.
- INFY.NS: Disagreement: ['portfolio_fit'] positive vs ['trend_following', 'volatility_risk'] negative.

## 🤔 Why no trade (selected)
- BAJFINANCE.NS (WATCH, 72.1): Final 72.1/100 -> WATCH [regime NEUTRAL]. Top: trend_following=90, relative_strength=90, portfolio_fit=80. NEUTRAL regime + modest confidence -> downgraded to WATCH.
- TITAN.NS (WATCH, 69.7): Final 69.7/100 -> WATCH [regime NEUTRAL]. Top: trend_following=88, portfolio_fit=80, relative_strength=76.
- ICICIBANK.NS (WATCH, 66.8): Final 66.8/100 -> WATCH [regime NEUTRAL]. Top: trend_following=93, portfolio_fit=80, breakout=70.
- SUNPHARMA.NS (WATCH, 66.0): Final 66.0/100 -> WATCH [regime NEUTRAL]. Top: trend_following=90, portfolio_fit=80, breakout=70.
- TECHM.NS (WATCH, 62.5): Final 62.5/100 -> WATCH [regime NEUTRAL]. Top: portfolio_fit=80, trend_following=78, breakout=70. Disagreement: ['trend_following', 'relative_strength', 'breakout', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- BHARTIARTL.NS (WATCH, 61.5): Final 61.5/100 -> WATCH [regime NEUTRAL]. Top: portfolio_fit=80, trend_following=76, news_event_risk=65.
- HCLTECH.NS (WATCH, 60.2): Final 60.2/100 -> WATCH [regime NEUTRAL]. Top: relative_strength=92, portfolio_fit=80, news_event_risk=65. Disagreement: ['relative_strength', 'portfolio_fit'] positive vs ['volatility_risk'] negative.
- SBIN.NS (NO_ACTION, 57.9): Final 57.9/100 -> NO_ACTION [regime NEUTRAL]. Top: portfolio_fit=80, news_event_risk=65, trend_following=58.

## 📊 Market-data usage
- Provider: `yfinance` · calls today: 108 · total this month: 648 (no API-key quota)

## 🧪 Data-quality warnings
- Already held — adding would require averaging (blocked) and reduces diversification.
- DataQuality:DATA_INSUFFICIENT
- Share price ₹11771 exceeds per-trade cap ₹10000.
- Share price ₹13783 exceeds per-trade cap ₹10000.
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