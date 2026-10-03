# Backtesting / Validation

This package is **honest by design**. It does not fabricate historical backtest
results.

## What v1 actually does

- **`cost_model.py` (real)** — estimates Indian equity *delivery* transaction
  costs (STT, exchange charges, GST, stamp duty, slippage, spread). Used by
  reports to show **cost-adjusted** paper P&L so results don't look
  unrealistically good.
- **`backtest_engine.py` → `PaperTradeReplay` (real)** — replays the trades the
  system *actually* made on paper and applies estimated costs. It only
  summarizes recorded paper activity — no simulated history.
- **`price_replay.py` → `PriceOnlyReplay` (real, descriptive)** — point-in-time
  replay of *price-based* strategies over ~2y yfinance bars. Each date is scored
  with `context.features.scoring_view` on bars up to that date (same math as the
  live trailing windows). **No news, no regime/portfolio gating, no costs.**
  CLI: `py -3 mmg.py backfill`. Output is labeled **not a profitability claim**
  (survivorship bias: current index membership). Feeds learning proposals as one
  input among several.

## What is a documented placeholder (intentionally)

- **`backtest_engine.py` → `replay_full_history()`** — a true full-pipeline
  historical backtest. Not implemented because doing it badly (survivorship
  bias, look-ahead bias, unrealistic fills, fabricated news) is worse than not
  doing it.
- **`walk_forward_validator.py`** — the correct anti-overfitting tool. Shipped as
  a skeleton so the project is structured for it.

## Before implementing the placeholders

Read [`docs/strategy_validation_principles.md`](../../docs/strategy_validation_principles.md).
Until a clean full-pipeline history exists, the **live paper run** plus
**price-only replay** are the validation tools — slow, explicit about limits.
