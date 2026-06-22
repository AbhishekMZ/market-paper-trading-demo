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

## What is a documented placeholder (intentionally)

- **`backtest_engine.py` → `replay_full_history()`** — a true historical
  backtest. Not implemented because doing it badly (survivorship bias,
  look-ahead bias, unrealistic fills) is worse than not doing it.
- **`walk_forward_validator.py`** — the correct anti-overfitting tool. Shipped as
  a skeleton so the project is structured for it.

## Before implementing the placeholders

Read [`docs/strategy_validation_principles.md`](../../docs/strategy_validation_principles.md).
You need a clean, point-in-time, survivorship-bias-free price history (the
SerpApi free tier does not provide one). Until then, the **one-month live paper
run is the validation** — slow, real, and unbiased.
