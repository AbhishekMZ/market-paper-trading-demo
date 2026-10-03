# Live-readiness checklist (human only)

Paper automation may eventually produce enough evidence to *discuss* live
trading. **Nothing in this repo auto-enables live orders.**

## Current standing (do not skip)

1. Readiness verdict in `decision_quality.json` is descriptive only and always
   reports `live_trading: "DISABLED"`.
2. `mmg.py learn propose` is **PROPOSAL — not applied**. It cannot set
   `allow_real_orders`, `live_trading_enabled`, or Angel One flags.
3. CI safety gate fails the run if any live flag is true.

## Minimum evidence before even considering a transition doc review

Use `config/evaluation.yml → readiness` as the floor, then raise the bar:

- [ ] ≥ 30 paper trades (not just 10)
- [ ] ≥ 40 distinct trading days
- [ ] Some **closed** paper exits (realized P&L), not only open marks
- [ ] Cost-adjusted paper return vs NIFTY not deeply negative
- [ ] Price-replay buy-grade edge not persistently negative (descriptive only)
- [ ] News / data-quality / historical-context blocks reviewed for false positives
- [ ] Full-universe scan coverage (`symbols_requested` ≈ `symbols_scored`) stable

## Manual go-live steps (future — not in v1)

See [`docs/future_real_trading_transition.md`](future_real_trading_transition.md).
Every `angel_one_safety_confirmations.*` flag must be flipped by a human, on a
non–GitHub-Actions host with a static IP. The learner must never set those flags.
