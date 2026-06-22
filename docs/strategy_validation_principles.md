# Strategy Validation Principles

The fastest way to lose real money is to trust a strategy that only ever
"worked" in a backtest or a single lucky month. This project is deliberately
conservative. Read this before changing weights, adding strategies, or even
*thinking* about real trading.

## The biases that kill retail algos

- **Overfitting.** Tuning thresholds until the demo month looks great fits noise,
  not signal. Out-of-sample, it falls apart. → *Do not tune thresholds to
  maximize one-month demo performance.*
- **Look-ahead bias.** Using information that wasn't available at decision time.
  → *Every signal stores a timestamp + data snapshot; we never use future data
  for a past decision, and we never rewrite a signal's reasoning after the
  outcome is known.*
- **Survivorship bias.** Testing only on stocks that still exist today ignores the
  ones that blew up. → *A real backtest needs a point-in-time, survivorship-free
  universe — which the free data tier does not provide. So we don't fake one.*
- **Ignoring costs/slippage.** Gross returns lie. → *`CostModel` applies estimated
  STT, exchange charges, GST, stamp duty, slippage, and spread; reports show
  cost-adjusted P&L.*
- **Trusting popularity.** "Everyone uses this indicator" is not evidence. → *Every
  strategy is a hypothesis in `config/research_hypotheses.yml` and must pass
  paper validation before its weight can grow.*

## Principles we follow

1. **Prefer fewer, higher-quality trades** over frequent trading (max 1 buy/day,
   5/month, score ≥ 80 to even consider a paper buy).
2. **Track no-trade and rejected decisions too** — they are part of the evidence.
   A strategy that avoids bad trades is doing its job.
3. **Out-of-sample before real money.** One month of live paper trading is the
   honest validation; treat it as a *start*, not a verdict.
4. **Don't over-trust one month.** Variance dominates small samples. The
   end-of-month report says so explicitly.

## Code-level guardrails (already enforced)

- Every signal includes a `timestamp` and a `data_snapshot`.
- The system never uses future data for past decisions.
- Old signal reasoning is never mutated after the outcome is known
  (signals are append-only in `signal_history.json`).
- Strategy weights are read from `config/scoring.yml` and are **not** changed
  automatically during the month.
- **No self-optimization** in v1. **No ML training** in v1. The strategy is
  deterministic, explainable, and boring on purpose.

## Why v1 avoids machine learning

ML adds opacity, overfitting risk, data-hunger, and a much larger surface for
silent failure — exactly the wrong trade-offs when the goal is to *understand*
whether a simple, explainable edge exists before risking money. A transparent
weighted rule set that a human can read line-by-line is the right tool for v1.
ML can be revisited only after a simple strategy is validated and the data
pipeline is trustworthy.

## Backtesting status

See [`src/backtesting/README.md`](../src/backtesting/README.md). v1 ships a real
**cost model** and a real **paper-trade replay**, but the full historical
backtester and walk-forward validator are honest **placeholders** — building
them on biased/free data would be worse than not building them. The live paper
run is the validation.
