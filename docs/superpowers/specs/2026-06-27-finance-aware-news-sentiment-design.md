# Finance-Aware News Sentiment — Design Spec

**Date:** 2026-06-27
**Status:** Approved (design) — pending spec review → implementation plan
**Branch:** `feature/finance-aware-sentiment` (off `main`)

## 1. Goal & Boundaries

**Goal:** Replace today's binary keyword sentiment with a finance-aware, confidence-scored
read that cannot be swung by a single noisy headline, and that surfaces *why* it
reached its verdict. This deepens news sentiment as a decision **input** while keeping
the system deterministic, explainable, and ₹0-cost.

**In scope**
- Severity-weighted lexicon (not flat keyword lists).
- Negation handling ("denies fraud" is not bearish).
- Entity relevance via proximity (a *peer's* bad news must not tank this stock).
- Recency weighting (fresher news weighs more).
- Cross-source agreement → a per-article **signed score (−1..+1) + confidence (0..1)**
  and a corroborated aggregate.
- One **shared scorer** used by both the risk overlay and the scoring plugin
  (removes today's duplicated keyword logic).

**Out of scope** (per brainstorming decisions)
- No ML model (deterministic lexicon only).
- No empirical backtest / forward-return validation of sentiment.
- Sentiment still **only adds caution** — it never creates or upgrades a buy.

**Non-negotiable safety invariants (must still hold after this change)**
- HIGH/CRITICAL adverse **events** still block a paper buy (deterministic event path).
- Positive news never creates/upgrades a buy and never changes the score in the overlay.
- No news → neutral no-op.
- CRITICAL news on a held position → EXIT_REVIEW (advisory; never auto-sells).
- CI **safety gate is untouched**: this change alters no config *flags*
  (`active_adapter`, `live_trading_enabled`, `allow_real_orders`, `angel_one_enabled`).
- No new or paid dependencies; pure-Python; fully offline-testable; degrades to neutral on any error.

## 2. Architecture — One Shared Scorer

Today sentiment logic is **duplicated**: the overlay (`src/news/sentiment.py`) and the
scoring plugin (`src/strategy/news_event_risk.py`) each carry their own keyword lists.
Both will instead call a single scorer.

```
                ┌──────────────────────────────────────────────┐
 text + ctx ──▶ │  score_text(text, cfg, relevance, age_hours, │
 (relevance,    │             company_tokens) -> SentimentScore │
  age, company) └──────────────────────────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                                ▼
  NewsRiskEngine._enrich (per NewsItem)        NewsEventRiskStrategy.evaluate
  → item.sentiment_score/confidence/label      (per headline string)
        │                                                │
        ▼                                                ▼
  aggregate(items) -> AggregateSentiment        aggregate(headline scores)
  (overall polarity, confidence,                → 0–100 score_contribution
   sources_agree, conflict, n_sources)            (calibrated, confidence-aware)
```

### New value object — `SentimentScore`
Lives in `src/news/sentiment.py`.

```
SentimentScore:
  polarity:   float        # −1..+1  (negative = bearish; caution-first asymmetry baked into weights)
  label:      NewsSentiment # NEGATIVE/NEUTRAL/POSITIVE, derived via neutral deadband
  confidence: float        # 0..1
  matched:    List[(term, weight)]
  negated:    List[str]    # terms neutralized by a negator (for the trace)
  reason:     str          # short human-readable explanation
```

### New aggregate object — `AggregateSentiment`
```
AggregateSentiment:
  label:         NewsSentiment
  polarity:      float       # relevance- & recency-weighted mean
  confidence:    float       # raised by multi-source agreement, cut by single-source/conflict
  sources_agree: bool
  conflict:      bool        # ≥1 source bearish AND ≥1 bullish
  n_sources:     int
  reason:        str
```

## 3. Components (each a small, pure, offline-testable function)

### 3.1 Weighted lexicon — `src/news/lexicon.py` (new)
- `load_lexicon(cfg) -> WeightedLexicon` with `.terms: Dict[str,float]` and `.negators: List[str]`.
- Built from config tiers, with **code-side defaults** so it works without config changes:
  - `critical_negative` (fraud, scam, ponzi, embezzle) → −1.0
  - `strong_negative` (probe, investigation, default, lawsuit, downgrade, insolvency) → −0.7
  - `mild_negative` (miss, weak results, profit warning, recall, fine) → −0.4
  - `mild_positive` (order win, upgrade, expansion, new contract) → +0.4
  - `strong_positive` (strong results, record profit, debt reduction, beats) → +0.6
- **Asymmetry:** positive ceilings are deliberately lower than negative magnitudes (caution-first).
- Back-compat: if only the legacy `negative_keywords`/`positive_keywords` lists are present,
  map them to default −0.6 / +0.4 weights.

### 3.2 Per-article scoring — `score_text(...)` in `src/news/sentiment.py`
1. Lowercase + tokenize (simple regex word split; keep token positions).
2. Match lexicon terms (single- and multi-word).
3. **Negation:** if a matched term has a negator within `negation_window` tokens before it,
   neutralize it (weight → 0) and record it in `negated`.
4. **Polarity:** saturating combine of surviving weights (e.g. `tanh(sum)`), clamped to −1..+1.
5. **Label:** `NEUTRAL` if `|polarity| < neutral_deadband`, else sign-based.
6. **Entity proximity:** using `company_tokens` (reuse `relevance.company_tokens`), measure
   nearest distance between a company token and a matched sentiment term. Near (≤ `window_tokens`)
   → small confidence boost; company absent / far from the bearish clause → confidence penalty
   (peer-mention guard). Folded into confidence only — never flips polarity.
7. **Confidence:** function of (number & strength of surviving matches, `relevance`, recency
   weight, entity-proximity). One weak match → low confidence; multiple strong concordant
   matches with the company named nearby → high.

### 3.3 Recency weighting
- `recency_weight(age_hours, cfg) -> 0..1`: full weight up to `recency.full_weight_hours`,
  linear decay to `recency.floor_weight` by `freshness.max_age_hours`. Used in aggregation
  and folded into per-article confidence.

### 3.4 Entity relevance — `src/news/relevance.py` (extended)
- Keep `relevance_score` (token-fraction) as the **noise gate** (`min_relevance`), unchanged.
- Reuse existing `company_tokens` inside the scorer for the proximity factor (§3.2 step 6).
  No change to the gate's behavior; proximity only modulates per-article confidence/weight.

### 3.5 Aggregation with cross-source agreement — `aggregate(...)`
- Polarity = mean of per-article polarities weighted by `relevance × recency_weight`.
- Group articles by `provider` (yfinance/gdelt). Determine each source's net sign.
- `sources_agree` = ≥2 distinct sources present and all non-neutral signs match.
- `conflict` = at least one source bearish and one bullish.
- Confidence: start from weighted-mean of per-article confidence, then
  `× (1 − single_source_penalty)` if only one source, `× (1 − conflict_penalty)` on conflict,
  `× (1 + agreement_bonus)` (clamped ≤ 1.0) when `sources_agree`.

## 4. How It Feeds Decisions (guardrail preserved, now confidence-aware)

### 4.1 Risk overlay — `src/news/news_risk_engine.py`
- `_enrich`: call `score_text(...)`; set `item.sentiment` (label), `item.sentiment_score`,
  `item.sentiment_confidence`; keep `matched_keywords`. Event classification path **unchanged**.
- `assess`: compute `AggregateSentiment`; populate new assessment fields (§5). `overall_sentiment`
  = aggregate label.
- **Hard blocks unchanged:** `blocks_buy` still derives from the deterministic event risk level
  (HIGH/CRITICAL). Safety-critical path is not touched.
- **Caution is never relaxed; sentiment is graded only where that is strictly safe:**
  - Hard blocks **and** the `requires_manual_review` trigger are left **exactly as today** — the
    overlay never weakens a caution. (`manual_review_min_confidence` is loaded for forward-use but
    is applied to no trigger in v1.)
  - `sentiment_boost` (informational, capped, never crosses the buy line) scales with confidence.
  - The "trustworthy, not twitchy" win lands in the **scoring plugin** (§4.2): a single
    low-confidence headline barely moves the 0–100 score instead of slamming it.
- Reasons include polarity, confidence, and agreement (e.g. "2 sources agree; confidence 0.82").

### 4.2 Scoring plugin — `src/strategy/news_event_risk.py`
- Drop its private keyword lists; score each headline via `score_text`, aggregate to
  `(polarity, confidence)`, then map **`effective = polarity × confidence`** → `score_contribution`
  via a sign-dependent linear interpolation around `neutral_base`:
  `score = neutral_base + effective × (max_positive − neutral_base)` when `effective ≥ 0`, and
  `score = neutral_base + effective × (neutral_base − min_negative)` when `effective < 0`
  (so effective 0 → ≈65, easing to `max_positive` ≈78 / `min_negative` ≈25 at the extremes),
  clamped 0–100. Multiplying by confidence is the "trustworthy, not twitchy" damping: a single
  low-confidence headline barely moves the score.
- ⚠️ **The one real behavior change:** this is a weighted (15/100) contributor, so some
  scores/labels will shift. That is the intended effect of a better input. Calibration knobs
  (`plugin_scoring`) keep the scale comparable so shifts are gradual, not wild.

## 5. Data Model & Export

- `src/news/base.py`:
  - `NewsItem` += `sentiment_score: float = 0.0`, `sentiment_confidence: float = 0.0`.
  - `NewsRiskAssessment` += `sentiment_score: float = 0.0`, `sentiment_confidence: float = 0.0`,
    `sentiment_sources_agree: bool = False`, `sentiment_conflict: bool = False`,
    `sentiment_n_sources: int = 0`.
  - Both `to_dict()` paths already serialize all dataclass fields → public/data payloads carry
    the new fields automatically.

## 6. Explainability Surfacing (minimal; conditional)

The user did **not** select the XAI-depth track, so FE work is intentionally tiny and **last**.
The News gate line in `frontend/src/components/DecisionTrace.jsx` shows
`sentiment · conf 0.8 · 2 sources agree` when present.

**Precondition:** `DecisionTrace.jsx` only exists on the unmerged **PR #9** branch
(`feature/simplified-xai-dashboard`). Therefore:
- The **backend (Tasks for §2–§5) is fully independent** of the frontend and ships first.
- The FE task is a clearly-marked **final, conditional** task, applied only after PR #9 merges
  (or rebased onto a `main` that includes it). It also requires the per-signal payload to carry
  `news_sentiment_confidence` + agreement (added in `apply_to_signal` + the signal serialization).
- If PR #9 stalls, the backend value is fully realized without this task.

## 7. Configuration (`config/news.yml`, all with code defaults → back-compat)

```yaml
sentiment:
  # legacy negative_keywords / positive_keywords retained as fallback
  weighted_terms:
    critical_negative: { weight: -1.0, terms: [fraud, scam, ponzi, embezzle, siphon] }
    strong_negative:   { weight: -0.7, terms: [probe, investigation, default, lawsuit, downgrade, insolvency, bankruptcy] }
    mild_negative:     { weight: -0.4, terms: [miss, weak results, profit warning, recall, fine, penalty] }
    mild_positive:     { weight:  0.4, terms: [order win, upgrade, expansion, new contract, wins order] }
    strong_positive:   { weight:  0.6, terms: [strong results, record profit, debt reduction, beats] }
  negators: [denies, denied, deny, no, not, cleared of, rejects, rejected, dismisses, dismissed, refutes, unfounded, false, without merit]
  negation_window: 4
  neutral_deadband: 0.15
  recency: { full_weight_hours: 24, floor_weight: 0.3 }
  entity_proximity: { window_tokens: 6, near_boost: 0.2, far_penalty: 0.3 }
  confidence:
    single_source_penalty: 0.3
    conflict_penalty: 0.5
    agreement_bonus: 0.25
    manual_review_min_confidence: 0.6
  plugin_scoring: { neutral_base: 65, max_positive: 78, min_negative: 25 }
```

## 8. Testing (TDD; existing standalone `scripts/test_*.py` convention)

Run style: `python scripts/test_<name>.py` → prints `OK: ...`, exit 0. No pytest, fully offline.

- **`scripts/test_sentiment_scorer.py` (new):**
  - weighted polarity ordering (fraud ≪ miss ≪ neutral ≪ order win ≪ strong results);
  - negation neutralizes ("denies fraud" → not bearish; records `negated`);
  - neutral deadband;
  - recency decay monotonic;
  - entity proximity boosts confidence when company named near the clause; peer-only mention lowers it;
  - confidence rises with concordant matches;
  - `aggregate`: two sources agreeing → higher confidence + `sources_agree`; bullish-vs-bearish → `conflict` + low confidence; single source → penalty;
  - back-compat: `classify_sentiment` and `aggregate_sentiment` still return the original enum-shaped results.
- **`scripts/test_news_risk_engine.py` (extend):**
  - all 5 existing cardinal invariants still pass unchanged;
  - new: the assessment carries finance-aware fields — CRITICAL fraud reads `sentiment_score < 0`;
    an order-win/strong-results headline reads `sentiment_score > 0`; positive news still does not
    block and never changes the score.
- **`scripts/test_news_event_risk_plugin.py` (new):** confidence-damped mapping — neutral headlines
  ≈65; strong negative <45 (NEGATIVE); strong positive >68 (POSITIVE); a single mild negative stays
  well above the strong-negative score (the not-twitchy win).
- Cross-source agreement/conflict/single-source are unit-tested directly in `aggregate` (the engine
  test stubs GDELT, so it sees a single source).

## 9. Error Handling

- Every new function degrades to a neutral `SentimentScore`/`AggregateSentiment` on bad input;
  never raises into the run (consistent with the existing "missing news → neutral" contract).
- Config parsing tolerates missing blocks (code defaults) and the legacy keyword lists.

## 10. File Map

| File | Change |
|------|--------|
| `src/news/lexicon.py` | **new** — weighted terms + negators loader (config + defaults) |
| `src/news/sentiment.py` | enhanced — `SentimentScore`, `AggregateSentiment`, `score_text`, `aggregate`; legacy wrappers kept |
| `src/news/relevance.py` | reuse `company_tokens` in scorer (no gate change) |
| `src/news/base.py` | new fields on `NewsItem` + `NewsRiskAssessment` |
| `src/news/news_risk_engine.py` | confidence-aware `_enrich` + `assess`; hard blocks unchanged |
| `src/strategy/news_event_risk.py` | use shared scorer; calibrated 0–100 mapping (the score-shift) |
| `config/news.yml` | `sentiment:` weighted/negation/recency/proximity/confidence/plugin blocks |
| `scripts/test_sentiment_scorer.py` | **new** unit tests |
| `scripts/test_news_risk_engine.py` | extended invariant + confidence tests |
| `frontend/src/components/DecisionTrace.jsx` | **final, conditional** — minimal sentiment/confidence/agreement line (needs PR #9) |

## 11. Deployment (parked)

Recommendation: **stay on GitHub Actions → Pages** (already ₹0, fits a pre-baked-JSON read-only
dashboard). Vercel/Render only earns its keep if a *live* backend API is later wanted (compute
sentiment on demand). Nothing in this design requires it; spec separately if/when desired.
