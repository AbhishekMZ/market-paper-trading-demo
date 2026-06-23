# News risk layer

> ⚠️ **Paper-trading only.** This layer can add caution to a paper decision. It
> can never place, create, or upgrade a buy, and the system never auto-sells in
> v1. No real orders exist.

## Overview & the one cardinal rule

The news risk layer is a **post-strategy risk overlay**. It runs *after* the
hybrid scoring engine has produced a score and a label for a symbol, and its only
job is to decide whether recent news should make the system **more** cautious.

One cardinal rule governs the whole layer, and it is enforced in code
(`src/news/news_risk_engine.py` → `apply_to_signal`):

> **News may DOWNGRADE or BLOCK a paper buy. News can NEVER create or upgrade a
> buy.**

A buy that the strategy engine already proposed can be downgraded to `WATCH`,
`MANUAL_REVIEW`, or `NO_ACTION`. A non-buy can never be lifted into a buy by news.
Positive news is recorded only as an informational `sentiment_boost` and is **not
added to the score** here. (The scoring layer's existing `news_event_risk` plugin
already grants a small positive nudge upstream; the risk overlay does not stack a
second one.) So **news alone can never trigger a buy.**

## Architecture (the `src/news/` module map)

```
src/news/
  base.py              NewsItem, NewsProvider (ABC), NewsRiskAssessment;
                       enums NewsSentiment / NewsRiskLevel / NewsEventType
  providers.py         YFinanceNewsProvider, GDELTNewsProvider, NewsAPIProvider (disabled)
  normalizer.py        parses the timestamp zoo (yfinance epoch / GDELT / ISO)
  deduper.py           collapses near-identical titles across providers
  relevance.py         company-token match; relevance threshold for GDELT
  sentiment.py         keyword sentiment (negative weighted over positive)
  event_classifier.py  text -> event type + risk, via config/news.yml event_rules
  cache.py             file-backed TTL cache so GDELT stays polite
  news_risk_engine.py  the orchestrator (gather -> assess -> apply_to_signal)
```

The orchestrator owns the pipeline; every other module is a small, single-purpose
step it composes. All thresholds, keywords, and rules live in `config/news.yml`,
not in code.

## Data flow / pipeline

Per symbol, the engine runs these steps:

```
  gather                dedupe          per-item               aggregate            apply
 ┌────────────┐       ┌────────┐      ┌─────────────┐       ┌──────────────┐    ┌─────────────┐
 │ yfinance   │       │ collapse│      │ relevance   │       │ NewsRisk     │    │ apply_to_   │
 │ snapshot   │──────▶│ near-   │─────▶│ + sentiment │──────▶│ Assessment   │───▶│ signal      │
 │ news       │       │ dup     │      │ + event     │       │ (worst-fresh │    │ (caution    │
 │ + GDELT    │       │ titles  │      │ classify    │       │  risk wins)  │    │  only)      │
 └────────────┘       └────────┘      └─────────────┘       └──────────────┘    └─────────────┘
```

1. **Gather** — pull headlines from the yfinance price snapshot (already fetched,
   zero extra cost) plus a GDELT query.
2. **Dedupe** — collapse near-identical titles across providers, preferring
   yfinance, then the freshest item.
3. **Per item** — score relevance (GDELT must clear a relevance threshold;
   yfinance is trusted since it is already symbol-tagged), score keyword
   sentiment, and classify the event type + risk.
4. **Aggregate** into a `NewsRiskAssessment`: `overall_sentiment`,
   `news_risk_level` (the **worst** risk across *fresh* items), `dominant_event_types`,
   `blocks_buy`, `requires_manual_review`, `exit_review_for_holding`, `reasons`,
   and `top_items`.
5. **Apply** — `apply_to_signal` maps the assessment to an action, adding caution
   only (see the table below).

## Providers

| Provider | Status | Cost | Notes |
|---|---|---|---|
| `YFinanceNewsProvider` | enabled | ₹0 | Reuses headlines already fetched with the price snapshot. No extra network call. yfinance is **unofficial**. |
| `GDELTNewsProvider` | enabled | ₹0 | GDELT 2.0 Doc API. Free, no key. 8 s timeout, file-backed TTL cache. Degrades to "no news" on any failure. |
| `NewsAPIProvider` | **disabled** | n/a | Needs `NEWSAPI_KEY`. Intentionally OFF in v1 to stay ₹0-cost. |

Reliability notes: GDELT is keyword-broad, so it is held to a relevance threshold
and cached (`cache.ttl_minutes`, default 60) to stay polite. Any provider failure
(timeout, parse error, empty result) degrades gracefully to "no news" for that
symbol. Missing news is treated as **neutral** — it never crashes a run and never
fabricates risk.

## Sentiment & event classification

Both are **keyword-driven, deterministic, and config-tunable — no ML.**

- **Sentiment** (`sentiment.py`) matches `config/news.yml → sentiment.negative_keywords`
  / `positive_keywords`. Negative keywords are weighted **over** positive ones, so
  the layer leans conservative by design.
- **Event classification** (`event_classifier.py`) maps text to an event type and
  a risk level via `event_rules` in the config (`FRAUD → CRITICAL`,
  `REGULATORY`/`LEGAL`/`RATING_DOWNGRADE → HIGH`, `MANAGEMENT_CHANGE`/`EARNINGS_MISS
  → MEDIUM`, `MACRO → LOW`, and `NONE` for clearly-positive events). When several
  rules match an item, the **worst risk wins.**

Because everything is keyword + config, the behaviour is reproducible and
auditable: the same headline always yields the same verdict, and tuning is a YAML
edit, not a code change.

## Verdict -> action mapping

`apply_to_signal` reads `config/news.yml → blocking` and maps the assessment to an
action. Every outcome only adds caution:

| News verdict | On a fresh **buy candidate** | On a **held position** |
|---|---|---|
| `CRITICAL` adverse | Buy **blocked** → downgraded to `NO_ACTION` | Flag `EXIT_REVIEW` (advisory; never auto-sells) |
| `HIGH` adverse | Buy **blocked** → downgraded to `WATCH` | (advisory review) |
| `MEDIUM` adverse | Downgraded to `MANUAL_REVIEW` | — |
| `LOW` / `NONE` / positive | No downgrade; positive news recorded as informational `sentiment_boost` only | — |

`EXIT_REVIEW` is **advisory** only: it surfaces a held position for human review
and an email alert. The system never places a sell in v1.

## Why news can never trigger a buy

Two invariants combine to guarantee this:

1. **Block-only invariant.** `apply_to_signal` is a one-way ratchet toward
   caution. Its transition table has no edge that *raises* a label — it can only
   move a buy down to `WATCH` / `MANUAL_REVIEW` / `NO_ACTION` (or leave it
   unchanged). There is no code path in which an input that was not a buy becomes
   a buy.
2. **Boost separation.** Positive news produces a capped, informational
   `sentiment_boost` (`scoring.positive_sentiment_boost_max`, default 3.0) that is
   reported for transparency but is **not** added to the strategy score and is
   **not** allowed to cross the buy threshold. The only positive contribution from
   news is the small nudge the `news_event_risk` strategy plugin already applied
   *upstream*, inside the normal scoring blend — well before this overlay runs.

So even a flood of glowing headlines cannot manufacture a buy. The worst the
overlay can do to a non-buy is leave it exactly where the strategy engine put it.

## Email alerts

Alerts go out **only by email** (Gmail SMTP) to the configured address — no
WhatsApp, Telegram, or push. Triggers (`config/news.yml → alerting.send_on`):

- `critical_news` — any `CRITICAL` news on a watched or held symbol.
- `high_risk_news_on_position` — `HIGH` news on a held bot position.
- `high_risk_news_blocked_buy` — `HIGH` news that blocked a would-be buy.

Alerts are throttled to `max_alerts_per_run` (default 5) so one noisy run cannot
spam the inbox. Every alert body reminds the reader: **PAPER TRADING ONLY, no real
order placed.**

## Configuration

All behaviour is in `config/news.yml` (loaded by `storage.load_all_configs()`):

| Key | What it controls |
|---|---|
| `news.enabled` | Master on/off for the overlay. |
| `providers.yfinance` / `providers.gdelt` / `providers.newsapi` | Per-provider enable, `max_items`, GDELT `lookback_hours` / `timeout_seconds` / `base_url`. NewsAPI stays disabled. |
| `cache.ttl_minutes` | How long GDELT results are cached per symbol. |
| `freshness.fresh_hours` / `max_age_hours` | What counts as "fresh" (can block) vs context-only. |
| `relevance.min_score` / `require_relevance_for_gdelt` / `keep_yfinance_unfiltered` | Relevance gating per source. |
| `blocking.*` | The HIGH/CRITICAL/MEDIUM → action rules and `EXIT_REVIEW` toggle. |
| `scoring.positive_sentiment_boost_max` | Cap on the informational boost (never crosses the buy threshold). |
| `sentiment.negative_keywords` / `positive_keywords` | Keyword lists for sentiment. |
| `event_rules` | text → (event type, risk) classification rules. |
| `alerting.*` | Email channel, recipient, `max_alerts_per_run`, and `send_on` triggers. |
| `export.*` | Caps on news items / assessments published to `public/data`. |

## Safety

- **Paper-only.** The overlay can add caution; it cannot place, upgrade, or create
  a buy, and the system never auto-sells in v1.
- **Defense in depth.** Even after the label is downgraded upstream,
  `src/execution_engine.py` independently **refuses** any buy whose
  `signal.news_blocks_buy` flag is set, emitting an audit event
  `PAPER_BUY_BLOCKED_BY_NEWS`. A bug that failed to downgrade a label would still
  be caught at execution.
- **Graceful degradation.** Provider failures degrade to "no news" (neutral).
  Missing news never crashes a run and never fabricates risk.
- **₹0-cost.** yfinance and GDELT are free and key-less; NewsAPI is disabled. No
  paid services, no secrets in config.

### Integration points

- `config/news.yml` — all thresholds, keywords, `event_rules`, alerting.
- `src/main.py` — runs the overlay **before** processing buys, persists artifacts,
  and emails alerts.
- `src/order_models.py` — `TradeSignal` carries `news_available`,
  `news_risk_level`, `news_sentiment`, `news_event_types`, `news_blocks_buy`,
  `news_item_count`, `news_top_headline`, `news_reasons`.
- `src/static_exporter.py` — publishes `news_assessments.json`, `news_items.json`,
  `news_alerts.json`, `news_health.json` to `public/data`.
- **Dashboard** — a "News" tab with `NewsRiskPanel`, `NewsEvents`, `NewsAlerts`,
  and `NewsSourceHealth`.
- **Demo** — `scripts/seed_sample_data.py` includes `SAMPLE_NEWS` (a positive ITC
  headline that does **not** force a buy; a `CRITICAL` SBIN "fraud probe" headline
  that blocks a buy) and stubs GDELT so seeding stays offline and deterministic.

## Limitations & future

- **Keyword sentiment is coarse.** It cannot read sarcasm, negation ("cleared of
  fraud"), or nuance, and it leans negative on purpose. It is a safety screen, not
  a sentiment model.
- **English-only, headline-only.** It reads titles, not full articles, and does
  not handle vernacular coverage.
- **GDELT is global and noisy.** The relevance threshold helps, but some
  off-topic items can still slip through (treated as caution, never as a buy).

Future, still **paper-only**, directions: per-source confidence weighting; an
India-focused news API once a free/affordable one is available; richer event
extraction. None of these would change the cardinal rule — news would still only
ever add caution.
