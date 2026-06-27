# Finance-Aware News Sentiment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace binary keyword news-sentiment with a deterministic, finance-aware scorer that emits a per-article signed score + confidence and a cross-source-corroborated aggregate, shared by the risk overlay and the scoring plugin — without relaxing any caution guardrail.

**Architecture:** A new `lexicon.py` (severity-weighted terms + negators) feeds `score_text()` in `sentiment.py`, which produces a `SentimentScore` (polarity −1..+1, label, confidence, matched/negated terms). `aggregate()` combines per-article scores into an `AggregateSentiment` whose confidence rises with cross-source agreement and falls on single-source/conflict. The overlay (`news_risk_engine.py`) exposes these as informational fields and scales only its informational positive boost by confidence — hard blocks and manual-review triggers are unchanged. The scoring plugin (`news_event_risk.py`) maps `polarity × confidence` onto its 0–100 contribution, so a single low-confidence headline no longer slams the score.

**Tech Stack:** Python 3.11, pure stdlib (`re`, `math`, `dataclasses`). No new dependencies. Tests are standalone scripts under `scripts/` run with `python scripts/test_*.py` (existing convention — no pytest).

---

## Safety invariants (must hold at every commit)

- HIGH/CRITICAL adverse **events** still block a paper buy (deterministic event-classifier path, untouched).
- Positive news never creates/upgrades a buy and never changes the score in the overlay.
- No news → neutral no-op.
- The overlay **never relaxes** an existing caution (no change to `blocks_buy` / `requires_manual_review` triggers). Confidence is informational + scales only the (already informational) positive boost.
- No config *flags* touched → CI safety gate untouched. No new deps. Deterministic.

## File Structure

| File | Responsibility |
|------|----------------|
| `src/news/lexicon.py` (new) | Weighted term map + negator list; load from config with code defaults. |
| `src/news/sentiment.py` (rewrite) | `SentimentScore`, `AggregateSentiment`, `score_text()`, `aggregate()`, `recency_weight()`, legacy wrappers. |
| `src/news/base.py` (edit) | New fields on `NewsItem` + `NewsRiskAssessment`. |
| `src/order_models.py` (edit) | New `news_sentiment_confidence` + `news_sentiment_sources_agree` on `TradeSignal`. |
| `src/news/news_risk_engine.py` (edit) | `_enrich`/`assess`/`apply_to_signal` use the new scorer; expose new fields; scale boost by confidence. |
| `src/strategy/news_event_risk.py` (rewrite) | Use shared scorer; confidence-damped 0–100 mapping. |
| `src/main.py` (edit) | Put `news_cfg` into the engine `context` so the plugin can reach it. |
| `config/news.yml` (edit) | `sentiment:` weighted/negation/recency/proximity/confidence/plugin blocks (defaults mirror code). |
| `scripts/test_sentiment_scorer.py` (new) | Unit tests for lexicon, scorer, aggregate, wrappers. |
| `scripts/test_news_event_risk_plugin.py` (new) | Plugin scoring/damping tests. |
| `scripts/test_news_risk_engine.py` (edit) | Keep 5 invariants; assert new assessment fields. |
| `frontend/src/components/DecisionTrace.jsx` (deferred) | Minimal sentiment·confidence·agreement line. Conditional on PR #9. |

---

### Task 1: Weighted lexicon module

**Files:**
- Create: `src/news/lexicon.py`
- Test: `scripts/test_sentiment_scorer.py`

- [ ] **Step 1: Write the failing test**

Create `scripts/test_sentiment_scorer.py`:

```python
"""Offline, deterministic tests for the finance-aware sentiment scorer.

Run:  python scripts/test_sentiment_scorer.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from news.lexicon import load_lexicon  # noqa: E402


def test_lexicon_defaults_and_overrides():
    lex = load_lexicon()
    assert lex.terms["fraud"] == -1.0
    assert lex.terms["miss"] == -0.4
    assert lex.terms["strong results"] == 0.6
    assert "denies" in lex.negators
    # config tiers override/extend defaults; defaults still present.
    lex2 = load_lexicon({"sentiment": {"weighted_terms": {
        "x": {"weight": -0.5, "terms": ["foo bar"]}}}})
    assert lex2.terms["foo bar"] == -0.5
    assert lex2.terms["fraud"] == -1.0


def main() -> int:
    test_lexicon_defaults_and_overrides()
    print("OK: sentiment scorer tests pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python scripts/test_sentiment_scorer.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'news.lexicon'`

- [ ] **Step 3: Write minimal implementation**

Create `src/news/lexicon.py`:

```python
"""Severity-weighted sentiment lexicon + negators.

Pure data + a loader. Defaults live in code so the scorer works with no config;
config tiers under news.yml -> sentiment.weighted_terms override/extend them.
Negative magnitudes intentionally exceed positive ceilings (caution-first).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

_DEFAULT_TIERS = {
    "critical_negative": (-1.0, ["fraud", "scam", "ponzi", "embezzle", "siphon", "forensic audit"]),
    "strong_negative": (-0.7, ["probe", "investigation", "default", "lawsuit", "downgrade", "insolvency", "bankruptcy"]),
    "mild_negative": (-0.4, ["miss", "weak results", "profit warning", "recall", "fine", "penalty"]),
    "mild_positive": (0.4, ["order win", "upgrade", "expansion", "new contract", "wins order"]),
    "strong_positive": (0.6, ["strong results", "record profit", "debt reduction", "beats"]),
}
_DEFAULT_NEGATORS = [
    "denies", "denied", "deny", "no", "not", "cleared of", "rejects", "rejected",
    "dismisses", "dismissed", "refutes", "unfounded", "false", "without merit",
]


@dataclass
class WeightedLexicon:
    terms: Dict[str, float] = field(default_factory=dict)
    negators: List[str] = field(default_factory=list)


def _sentiment_block(cfg: Any) -> Dict[str, Any]:
    if isinstance(cfg, dict):
        return cfg.get("sentiment") or {}
    return {}


def load_lexicon(cfg: Any = None) -> WeightedLexicon:
    """Build the lexicon: code defaults, then config tier + legacy overrides."""
    terms: Dict[str, float] = {}
    for _, (weight, words) in _DEFAULT_TIERS.items():
        for t in words:
            terms[t] = weight

    s = _sentiment_block(cfg)
    wt = s.get("weighted_terms")
    if isinstance(wt, dict):
        for _, spec in wt.items():
            if not isinstance(spec, dict):
                continue
            w = float(spec.get("weight", 0.0))
            for t in spec.get("terms", []) or []:
                terms[str(t).lower()] = w

    # Legacy flat lists are a fallback — only fill terms not already weighted.
    for t in s.get("negative_keywords", []) or []:
        terms.setdefault(str(t).lower(), -0.6)
    for t in s.get("positive_keywords", []) or []:
        terms.setdefault(str(t).lower(), 0.4)

    negators = [str(n).lower() for n in (s.get("negators") or _DEFAULT_NEGATORS)]
    return WeightedLexicon(terms=terms, negators=negators)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python scripts/test_sentiment_scorer.py`
Expected: `OK: sentiment scorer tests pass`

- [ ] **Step 5: Commit**

```bash
git add src/news/lexicon.py scripts/test_sentiment_scorer.py
git commit -m "feat(news): severity-weighted sentiment lexicon + loader"
```

---

### Task 2: Core scorer — `SentimentScore` + `score_text` (weighting + deadband)

**Files:**
- Modify: `src/news/sentiment.py`
- Test: `scripts/test_sentiment_scorer.py`

- [ ] **Step 1: Write the failing test**

Add to `scripts/test_sentiment_scorer.py` (new import + function, and call it in `main`):

```python
from news.sentiment import SentimentScore, score_text  # noqa: E402
from news.base import NewsSentiment  # noqa: E402


def test_score_text_weighting_and_deadband():
    neg = score_text("Company hit by fraud probe")
    assert neg.label == NewsSentiment.NEGATIVE and neg.polarity < 0
    pos = score_text("Company posts strong results and record profit")
    assert pos.label == NewsSentiment.POSITIVE and pos.polarity > 0
    flat = score_text("The company held its annual general meeting today")
    assert flat.label == NewsSentiment.NEUTRAL and abs(flat.polarity) < 0.15
    # severity ordering: fraud is more bearish than a mild miss.
    assert score_text("fraud probe").polarity < score_text("earnings miss").polarity
    # positive ceiling stays below negative magnitude (caution-first).
    assert abs(pos.polarity) < abs(score_text("fraud scam probe").polarity)
```

Update `main()`:

```python
def main() -> int:
    test_lexicon_defaults_and_overrides()
    test_score_text_weighting_and_deadband()
    print("OK: sentiment scorer tests pass")
    return 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python scripts/test_sentiment_scorer.py`
Expected: FAIL with `ImportError: cannot import name 'score_text' from 'news.sentiment'`

- [ ] **Step 3: Write minimal implementation**

Replace the entire contents of `src/news/sentiment.py` with:

```python
"""Finance-aware news sentiment scorer (deterministic, explainable, no ML).

`score_text` turns one headline/summary into a SentimentScore: a signed polarity
in [-1, +1], a label, and a confidence in [0, 1], plus the terms that drove it.
`aggregate` combines per-article scores, raising confidence on cross-source
agreement and cutting it on single-source / conflicting reads. Negative news is
weighted more heavily than positive — the system is never talked into optimism.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from news.base import NewsSentiment
from news.lexicon import load_lexicon

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _sent_cfg(cfg: Any) -> Dict[str, Any]:
    if isinstance(cfg, dict):
        return cfg.get("sentiment") or {}
    return {}


def _label_for(polarity: float, deadband: float) -> NewsSentiment:
    if abs(polarity) < deadband:
        return NewsSentiment.NEUTRAL
    return NewsSentiment.POSITIVE if polarity > 0 else NewsSentiment.NEGATIVE


@dataclass
class SentimentScore:
    polarity: float = 0.0
    label: NewsSentiment = NewsSentiment.NEUTRAL
    confidence: float = 0.0
    matched: List[Tuple[str, float]] = field(default_factory=list)
    negated: List[str] = field(default_factory=list)
    reason: str = ""


def score_text(text: str, cfg: Any = None, *, relevance: float = 1.0,
               age_hours: Optional[float] = None,
               company_tokens: Optional[List[str]] = None) -> SentimentScore:
    low = (text or "").lower()
    if not low.strip():
        return SentimentScore(reason="empty text -> neutral")
    lex = load_lexicon(cfg)
    deadband = float(_sent_cfg(cfg).get("neutral_deadband", 0.15))

    surviving: List[Tuple[str, float]] = []
    for term, w in lex.terms.items():
        if re.search(r"\b" + re.escape(term), low):
            surviving.append((term, w))

    total = sum(w for _, w in surviving)
    polarity = math.tanh(total)
    label = _label_for(polarity, deadband)

    strength = sum(abs(w) for _, w in surviving)
    conf = _clamp(min(1.0, strength / 1.5) * float(relevance), 0.0, 1.0)
    if not surviving:
        conf = min(conf, 0.1)

    reason = f"matched={surviving}; polarity={polarity:.2f}, confidence={conf:.2f}"
    return SentimentScore(round(polarity, 3), label, round(conf, 3),
                          list(surviving), [], reason)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python scripts/test_sentiment_scorer.py`
Expected: `OK: sentiment scorer tests pass`

- [ ] **Step 5: Commit**

```bash
git add src/news/sentiment.py scripts/test_sentiment_scorer.py
git commit -m "feat(news): weighted score_text with polarity + neutral deadband"
```

---

### Task 3: Negation, recency, and entity-proximity in `score_text`

**Files:**
- Modify: `src/news/sentiment.py`
- Test: `scripts/test_sentiment_scorer.py`

- [ ] **Step 1: Write the failing test**

Add to `scripts/test_sentiment_scorer.py` (new import + functions, and call them in `main`):

```python
from news.sentiment import recency_weight  # noqa: E402
from news.relevance import company_tokens  # noqa: E402


def test_negation_neutralizes():
    s = score_text("Company denies fraud allegations")
    assert s.label == NewsSentiment.NEUTRAL and "fraud" in s.negated
    s2 = score_text("Company hit by fraud probe")
    assert s2.label == NewsSentiment.NEGATIVE and not s2.negated


def test_recency_decay():
    fresh = recency_weight(1)
    mid = recency_weight(60)
    old = recency_weight(500)
    assert fresh == 1.0
    assert 0.3 <= mid < 1.0
    assert old == 0.3
    assert fresh > mid > old


def test_entity_proximity_confidence():
    toks = company_tokens("RELIANCE.NS", "Reliance Industries")
    near = score_text("Reliance hit by fraud probe", company_tokens=toks)
    far = score_text("Tata Steel fraud probe widens across the sector", company_tokens=toks)
    # same bearish terms; confidence higher when the company is named near them.
    assert near.confidence > far.confidence
```

Update `main()`:

```python
def main() -> int:
    test_lexicon_defaults_and_overrides()
    test_score_text_weighting_and_deadband()
    test_negation_neutralizes()
    test_recency_decay()
    test_entity_proximity_confidence()
    print("OK: sentiment scorer tests pass")
    return 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python scripts/test_sentiment_scorer.py`
Expected: FAIL — `ImportError: cannot import name 'recency_weight'` (and, once added, the negation/proximity assertions fail against the Task 2 scorer).

- [ ] **Step 3: Write minimal implementation**

In `src/news/sentiment.py`, add `recency_weight` (place it just after `_label_for`) and replace `score_text` with the full version.

Add:

```python
def recency_weight(age_hours: Optional[float], cfg: Any = None) -> float:
    """1.0 for fresh items, decaying linearly to floor_weight by max_age_hours."""
    if age_hours is None:
        return 1.0
    s = _sent_cfg(cfg).get("recency", {})
    full = float(s.get("full_weight_hours", 24))
    floor = float(s.get("floor_weight", 0.3))
    fr = cfg.get("freshness", {}) if isinstance(cfg, dict) else {}
    max_age = float(fr.get("max_age_hours", 96))
    if age_hours <= full or max_age <= full:
        return 1.0 if age_hours <= full else floor
    if age_hours >= max_age:
        return floor
    frac = (age_hours - full) / (max_age - full)
    return 1.0 - frac * (1.0 - floor)
```

Replace `score_text` with:

```python
def score_text(text: str, cfg: Any = None, *, relevance: float = 1.0,
               age_hours: Optional[float] = None,
               company_tokens: Optional[List[str]] = None) -> SentimentScore:
    low = (text or "").lower()
    if not low.strip():
        return SentimentScore(reason="empty text -> neutral")
    lex = load_lexicon(cfg)
    sent = _sent_cfg(cfg)
    deadband = float(sent.get("neutral_deadband", 0.15))
    window = int(sent.get("negation_window", 4))

    tokens = [(m.group(0), m.start()) for m in _TOKEN_RE.finditer(low)]
    token_starts = [s for _, s in tokens]

    def tok_index(char_pos: int) -> int:
        idx = 0
        for i, s in enumerate(token_starts):
            if s <= char_pos:
                idx = i
            else:
                break
        return idx

    surviving: List[Tuple[str, float, int]] = []
    negated: List[str] = []
    for term, w in lex.terms.items():
        m = re.search(r"\b" + re.escape(term), low)
        if not m:
            continue
        start = m.start()
        lo = max(0, tok_index(start) - window)
        win_text = low[token_starts[lo]:start] if token_starts else ""
        if any(re.search(r"\b" + re.escape(n), win_text) for n in lex.negators):
            negated.append(term)
            continue
        surviving.append((term, w, start))

    total = sum(w for _, w, _ in surviving)
    polarity = math.tanh(total)
    label = _label_for(polarity, deadband)

    strength = sum(abs(w) for _, w, _ in surviving)
    base = min(1.0, strength / 1.5)

    prox_factor = 1.0
    if company_tokens:
        ep = sent.get("entity_proximity", {})
        near_boost = float(ep.get("near_boost", 0.2))
        far_pen = float(ep.get("far_penalty", 0.3))
        pwin = int(ep.get("window_tokens", 6))
        comp_idx = [tok_index(mm.start()) for mm in
                    (re.search(r"\b" + re.escape(ct), low) for ct in company_tokens) if mm]
        if not comp_idx:
            prox_factor = 1.0 - far_pen
        elif surviving:
            term_idx = [tok_index(s) for _, _, s in surviving]
            nearest = min(abs(a - b) for a in term_idx for b in comp_idx)
            prox_factor = (1.0 + near_boost) if nearest <= pwin else (1.0 - far_pen)

    rec = recency_weight(age_hours, cfg)
    conf = _clamp(base * float(relevance) * rec * prox_factor, 0.0, 1.0)
    if not surviving:
        conf = min(conf, 0.1)

    matched = [(t, w) for t, w, _ in surviving]
    reason = (f"matched={matched}" + (f"; negated={negated}" if negated else "")
              + f"; polarity={polarity:.2f}, confidence={conf:.2f}")
    return SentimentScore(round(polarity, 3), label, round(conf, 3), matched, negated, reason)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python scripts/test_sentiment_scorer.py`
Expected: `OK: sentiment scorer tests pass`

- [ ] **Step 5: Commit**

```bash
git add src/news/sentiment.py scripts/test_sentiment_scorer.py
git commit -m "feat(news): negation, recency decay, entity-proximity confidence"
```

---

### Task 4: `aggregate()` with cross-source agreement

**Files:**
- Modify: `src/news/sentiment.py`
- Test: `scripts/test_sentiment_scorer.py`

- [ ] **Step 1: Write the failing test**

Add to `scripts/test_sentiment_scorer.py` (new import + function, and call it in `main`):

```python
from news.sentiment import AggregateSentiment, aggregate  # noqa: E402


def test_aggregate_agreement_and_conflict():
    # records: (polarity, confidence, provider, relevance, age_hours)
    agree = aggregate([(-0.8, 0.9, "yfinance", 1.0, 1.0), (-0.7, 0.8, "gdelt", 0.9, 2.0)])
    assert agree.label == NewsSentiment.NEGATIVE and agree.sources_agree and not agree.conflict
    assert agree.n_sources == 2 and agree.confidence > 0.7

    conflict = aggregate([(-0.8, 0.9, "yfinance", 1.0, 1.0), (0.7, 0.8, "gdelt", 1.0, 1.0)])
    assert conflict.conflict and conflict.confidence < 0.6

    single = aggregate([(-0.8, 0.9, "yfinance", 1.0, 1.0)])
    assert single.n_sources == 1 and single.confidence < 0.9 and single.label == NewsSentiment.NEGATIVE

    empty = aggregate([])
    assert empty.label == NewsSentiment.NEUTRAL and empty.n_sources == 0
```

Update `main()` to call `test_aggregate_agreement_and_conflict()` (add the line before the print).

- [ ] **Step 2: Run test to verify it fails**

Run: `python scripts/test_sentiment_scorer.py`
Expected: FAIL with `ImportError: cannot import name 'aggregate' from 'news.sentiment'`

- [ ] **Step 3: Write minimal implementation**

In `src/news/sentiment.py`, add at the end:

```python
@dataclass
class AggregateSentiment:
    label: NewsSentiment = NewsSentiment.NEUTRAL
    polarity: float = 0.0
    confidence: float = 0.0
    sources_agree: bool = False
    conflict: bool = False
    n_sources: int = 0
    reason: str = ""


def aggregate(records: List[Tuple[float, float, str, float, Optional[float]]],
              cfg: Any = None) -> AggregateSentiment:
    """Combine per-article (polarity, confidence, provider, relevance, age_hours).

    Confidence rises when ≥2 distinct sources agree, falls on single-source or
    when sources conflict. Polarity is a relevance×recency-weighted mean.
    """
    sent = _sent_cfg(cfg)
    deadband = float(sent.get("neutral_deadband", 0.15))
    cc = sent.get("confidence", {})
    single_pen = float(cc.get("single_source_penalty", 0.3))
    conflict_pen = float(cc.get("conflict_penalty", 0.5))
    agree_bonus = float(cc.get("agreement_bonus", 0.25))

    if not records:
        return AggregateSentiment(confidence=0.1, reason="no items -> neutral")

    weights = [max(0.0, float(rel)) * recency_weight(age, cfg)
               for (_pol, _conf, _prov, rel, age) in records]
    tw = sum(weights)
    if tw > 0:
        pol_mean = sum(w * r[0] for r, w in zip(records, weights)) / tw
        conf_mean = sum(w * r[1] for r, w in zip(records, weights)) / tw
    else:
        pol_mean = sum(r[0] for r in records) / len(records)
        conf_mean = sum(r[1] for r in records) / len(records)

    by_source: Dict[str, float] = {}
    for pol, _conf, prov, _rel, _age in records:
        by_source[prov] = by_source.get(prov, 0.0) + pol
    signs = {p: (-1 if s < -deadband else 1 if s > deadband else 0) for p, s in by_source.items()}
    non_neutral = [v for v in signs.values() if v != 0]
    n_sources = len(by_source)
    sources_agree = len(non_neutral) >= 2 and len(set(non_neutral)) == 1
    conflict = (1 in non_neutral) and (-1 in non_neutral)

    conf = conf_mean
    if conflict:
        conf *= (1.0 - conflict_pen)
    elif sources_agree:
        conf = min(1.0, conf * (1.0 + agree_bonus))
    elif n_sources < 2:
        conf *= (1.0 - single_pen)

    label = _label_for(pol_mean, deadband)
    reason = (f"{len(records)} item(s)/{n_sources} source(s); polarity {pol_mean:.2f}, "
              f"confidence {conf:.2f}"
              + ("; sources agree" if sources_agree else "")
              + ("; sources conflict" if conflict else ""))
    return AggregateSentiment(label, round(pol_mean, 3), round(_clamp(conf, 0.0, 1.0), 3),
                              sources_agree, conflict, n_sources, reason)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python scripts/test_sentiment_scorer.py`
Expected: `OK: sentiment scorer tests pass`

- [ ] **Step 5: Commit**

```bash
git add src/news/sentiment.py scripts/test_sentiment_scorer.py
git commit -m "feat(news): cross-source aggregate sentiment with confidence"
```

---

### Task 5: Back-compat wrappers (`classify_sentiment`, `aggregate_sentiment`)

**Files:**
- Modify: `src/news/sentiment.py`
- Test: `scripts/test_sentiment_scorer.py`

- [ ] **Step 1: Write the failing test**

Add to `scripts/test_sentiment_scorer.py` (new import + function, and call it in `main`):

```python
from news.sentiment import classify_sentiment, aggregate_sentiment  # noqa: E402


def test_backcompat_wrappers():
    label, neg, pos = classify_sentiment("fraud probe", {})
    assert label == NewsSentiment.NEGATIVE
    assert "fraud" in neg and "probe" in neg and pos == []
    assert aggregate_sentiment([NewsSentiment.POSITIVE, NewsSentiment.NEGATIVE]) == NewsSentiment.NEGATIVE
    assert aggregate_sentiment([]) == NewsSentiment.NEUTRAL
```

Update `main()` to call `test_backcompat_wrappers()` before the print.

- [ ] **Step 2: Run test to verify it fails**

Run: `python scripts/test_sentiment_scorer.py`
Expected: FAIL with `ImportError: cannot import name 'classify_sentiment' from 'news.sentiment'`

- [ ] **Step 3: Write minimal implementation**

In `src/news/sentiment.py`, add at the end:

```python
def classify_sentiment(text: str, cfg: Any) -> Tuple[NewsSentiment, List[str], List[str]]:
    """Legacy shape: (label, matched_negative, matched_positive). Delegates to score_text."""
    sc = score_text(text, cfg)
    neg = sorted(t for t, w in sc.matched if w < 0)
    pos = sorted(t for t, w in sc.matched if w > 0)
    return sc.label, neg, pos


def aggregate_sentiment(sentiments: List[NewsSentiment]) -> NewsSentiment:
    """Legacy label-only combine: any negative dominates (caution-first)."""
    if not sentiments:
        return NewsSentiment.NEUTRAL
    if any(s == NewsSentiment.NEGATIVE for s in sentiments):
        return NewsSentiment.NEGATIVE
    if any(s == NewsSentiment.POSITIVE for s in sentiments):
        return NewsSentiment.POSITIVE
    return NewsSentiment.NEUTRAL
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python scripts/test_sentiment_scorer.py`
Expected: `OK: sentiment scorer tests pass`

- [ ] **Step 5: Commit**

```bash
git add src/news/sentiment.py scripts/test_sentiment_scorer.py
git commit -m "feat(news): keep legacy classify_sentiment/aggregate_sentiment wrappers"
```

---

### Task 6: Config — `sentiment:` blocks in `config/news.yml`

**Files:**
- Modify: `config/news.yml`

- [ ] **Step 1: Add the config (no test — defaults already mirror these values)**

In `config/news.yml`, inside the existing `sentiment:` mapping (it currently holds
`negative_keywords:` and `positive_keywords:` lists — keep those), add these keys at
the same indentation level as `negative_keywords:`:

```yaml
    # --- finance-aware scorer (deterministic). Values mirror code defaults. ---
    weighted_terms:
      critical_negative: { weight: -1.0, terms: [fraud, scam, ponzi, embezzle, siphon, forensic audit] }
      strong_negative:   { weight: -0.7, terms: [probe, investigation, default, lawsuit, downgrade, insolvency, bankruptcy] }
      mild_negative:     { weight: -0.4, terms: [miss, weak results, profit warning, recall, fine, penalty] }
      mild_positive:     { weight:  0.4, terms: [order win, upgrade, expansion, new contract, wins order] }
      strong_positive:   { weight:  0.6, terms: [strong results, record profit, debt reduction, beats] }
    negators: [denies, denied, deny, "no", "not", cleared of, rejects, rejected, dismisses, dismissed, refutes, unfounded, "false", without merit]
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

- [ ] **Step 2: Verify the file still parses**

Run: `python -c "import yaml; yaml.safe_load(open('config/news.yml'))" && echo OK`
Expected: `OK`

- [ ] **Step 3: Verify the scorer reads the config consistently**

Run:
```bash
python -c "import sys; sys.path.insert(0,'src'); import storage; from news.sentiment import score_text; c=storage.load_config('news.yml')['news']; print(score_text('fraud probe', c).label.value)"
```
Expected: `NEGATIVE`

- [ ] **Step 4: Commit**

```bash
git add config/news.yml
git commit -m "feat(news): config blocks for weighted sentiment scorer"
```

---

### Task 7: Data-model fields (`NewsItem`, `NewsRiskAssessment`, `TradeSignal`)

**Files:**
- Modify: `src/news/base.py:82-101` (NewsItem) and `:109-129` (NewsRiskAssessment)
- Modify: `src/order_models.py:231-239` (TradeSignal news fields)

- [ ] **Step 1: Add fields to `NewsItem`**

In `src/news/base.py`, in the `NewsItem` dataclass, add two fields immediately after
the `sentiment: NewsSentiment = NewsSentiment.NEUTRAL` line:

```python
    sentiment_score: float = 0.0        # -1..+1 signed polarity
    sentiment_confidence: float = 0.0   # 0..1
```

- [ ] **Step 2: Add fields to `NewsRiskAssessment`**

In `src/news/base.py`, in the `NewsRiskAssessment` dataclass, add these fields
immediately after the `overall_sentiment: NewsSentiment = NewsSentiment.NEUTRAL` line:

```python
    sentiment_score: float = 0.0
    sentiment_confidence: float = 0.0
    sentiment_sources_agree: bool = False
    sentiment_conflict: bool = False
    sentiment_n_sources: int = 0
```

- [ ] **Step 3: Add fields to `TradeSignal`**

In `src/order_models.py`, in the `TradeSignal` dataclass, add two fields immediately
after the `news_sentiment: str = "NEUTRAL"` line:

```python
    news_sentiment_confidence: float = 0.0
    news_sentiment_sources_agree: bool = False
```

- [ ] **Step 4: Verify dataclasses still construct and serialize**

Run:
```bash
python -c "import sys; sys.path.insert(0,'src'); from news.base import NewsItem, NewsRiskAssessment; from order_models import TradeSignal, SignalLabel, RiskLevel, DataQuality; \
i=NewsItem(symbol='X', title='t', source='s', provider='p'); \
a=NewsRiskAssessment(symbol='X'); \
print(i.sentiment_score, i.sentiment_confidence, a.sentiment_sources_agree, a.sentiment_n_sources); \
print('news_sentiment_confidence' in TradeSignal('i','X','n','NSE',1.0,SignalLabel.WATCH,RiskLevel.LOW,0.5,DataQuality.GOOD,'r').to_dict())"
```
Expected: `0.0 0.0 False 0` then `True`

- [ ] **Step 5: Commit**

```bash
git add src/news/base.py src/order_models.py
git commit -m "feat(news): sentiment score/confidence/agreement fields on models"
```

---

### Task 8: Confidence-aware overlay (`news_risk_engine.py`)

**Files:**
- Modify: `src/news/news_risk_engine.py` (imports, `__init__`, `_enrich`, `assess`, `apply_to_signal`)
- Test: `scripts/test_news_risk_engine.py`

- [ ] **Step 1: Write the failing test**

In `scripts/test_news_risk_engine.py`, add these assertions to `main()` immediately
before the final `print("OK: ...")` line:

```python
    # 6) New: assessment carries finance-aware sentiment fields.
    assert a.sentiment_score < 0, "CRITICAL fraud news must read negative"
    assert 0.0 <= a.sentiment_confidence <= 1.0
    assert a2.sentiment_score > 0, "order-win/strong-results must read positive"
    # Overlay never relaxes caution: positive news still does not block or change score.
    assert not a2.blocks_buy and s2.score == 85.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python scripts/test_news_risk_engine.py`
Expected: FAIL with `AttributeError: 'NewsRiskAssessment' object has no attribute 'sentiment_score'` is already provided by Task 7, so instead it fails on `assert a.sentiment_score < 0` (currently `0.0`, the engine doesn't populate it yet).

- [ ] **Step 3: Update imports and `__init__`**

In `src/news/news_risk_engine.py`, change the two import lines:

```python
from news.relevance import relevance_score
```
to:
```python
from news.relevance import company_tokens, relevance_score
```

and:
```python
from news.sentiment import aggregate_sentiment, classify_sentiment
```
to:
```python
from news.sentiment import aggregate, score_text
```

In `__init__`, add after the `self.boost_cap = ...` line:

```python
        sent = cfg.get("sentiment", {})
        self.manual_review_min_conf = float(
            sent.get("confidence", {}).get("manual_review_min_confidence", 0.6))
```

- [ ] **Step 4: Replace `_enrich`**

Replace the `_enrich` method with:

```python
    def _enrich(self, item: NewsItem, symbol, company_name) -> None:
        text = f"{item.title} {item.summary}".strip()
        item.relevance = (
            1.0 if item.provider == "yfinance" else relevance_score(text, symbol, company_name)
        )
        score = score_text(
            text, self.cfg,
            relevance=item.relevance,
            age_hours=item.age_hours,
            company_tokens=company_tokens(symbol, company_name),
        )
        item.sentiment = score.label
        item.sentiment_score = score.polarity
        item.sentiment_confidence = score.confidence
        types, risk, matched = classify_events(text, self.cfg)
        item.event_types = types
        item.risk_level = risk
        item.matched_keywords = sorted({t for t, _ in score.matched} | set(matched))
```

- [ ] **Step 5: Update `assess` aggregation and the returned assessment**

In `assess`, replace this line:

```python
        overall_sentiment = aggregate_sentiment([it.sentiment for it in blocking_pool])
```
with:
```python
        agg = aggregate(
            [(it.sentiment_score, it.sentiment_confidence, it.provider, it.relevance, it.age_hours)
             for it in blocking_pool],
            self.cfg,
        )
        overall_sentiment = agg.label
```

Replace the positive-boost block:

```python
        boost = 0.0
        if not blocks_buy and overall_sentiment == NewsSentiment.POSITIVE and worst == NewsRiskLevel.NONE:
            boost = min(self.boost_cap, 1.0 + 0.5 * fresh_count)
```
with:
```python
        boost = 0.0
        if not blocks_buy and overall_sentiment == NewsSentiment.POSITIVE and worst == NewsRiskLevel.NONE:
            # Informational only; scaled by confidence. Never crosses the buy line.
            boost = min(self.boost_cap, (1.0 + 0.5 * fresh_count) * agg.confidence)
```

In the `return NewsRiskAssessment(...)` call, add these keyword arguments
immediately after `sentiment_boost=round(boost, 2),`:

```python
            sentiment_score=agg.polarity,
            sentiment_confidence=agg.confidence,
            sentiment_sources_agree=agg.sources_agree,
            sentiment_conflict=agg.conflict,
            sentiment_n_sources=agg.n_sources,
```

- [ ] **Step 6: Populate the new signal fields in `apply_to_signal`**

In `apply_to_signal`, add after the `signal.news_sentiment = assessment.overall_sentiment.value` line:

```python
        signal.news_sentiment_confidence = round(assessment.sentiment_confidence, 2)
        signal.news_sentiment_sources_agree = assessment.sentiment_sources_agree
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python scripts/test_news_risk_engine.py`
Expected: `OK: all news risk engine invariants hold.`

Also re-run the scorer suite to confirm nothing regressed:
Run: `python scripts/test_sentiment_scorer.py`
Expected: `OK: sentiment scorer tests pass`

- [ ] **Step 8: Commit**

```bash
git add src/news/news_risk_engine.py scripts/test_news_risk_engine.py
git commit -m "feat(news): confidence-aware overlay; expose sentiment score/agreement"
```

---

### Task 9: Scoring-plugin unification + `context.news_cfg`

**Files:**
- Modify: `src/main.py:235-247` (add `news_cfg` to context)
- Modify: `src/strategy/news_event_risk.py` (use shared scorer)
- Test: `scripts/test_news_event_risk_plugin.py` (new)

- [ ] **Step 1: Write the failing test**

Create `scripts/test_news_event_risk_plugin.py`:

```python
"""Offline tests for the news_event_risk scoring plugin (shared sentiment scorer).

Run:  python scripts/test_news_event_risk_plugin.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import storage  # noqa: E402
from strategy.news_event_risk import NewsEventRiskStrategy  # noqa: E402
from strategy.base import NEGATIVE, NEUTRAL, POSITIVE  # noqa: E402


def _ctx():
    return {"news_cfg": storage.load_config("news.yml").get("news", {})}


def _md(headlines):
    return {"headlines": headlines}


def main() -> int:
    p = NewsEventRiskStrategy()
    ctx = _ctx()

    none = p.evaluate("X", _md([]), {}, ctx)
    assert none.score_contribution == 65.0 and none.signal == NEUTRAL

    strong_neg = p.evaluate("X", _md(["Company hit by fraud probe; forensic audit"]), {}, ctx)
    assert strong_neg.signal == NEGATIVE and strong_neg.score_contribution < 45

    strong_pos = p.evaluate("X", _md(["Strong results, record profit; debt reduction"]), {}, ctx)
    assert strong_pos.signal == POSITIVE and strong_pos.score_contribution > 68

    # A single mild negative is damped by low confidence — not slammed.
    mild_neg = p.evaluate("X", _md(["Q3 profit misses estimates"]), {}, ctx)
    assert mild_neg.score_contribution > strong_neg.score_contribution
    assert mild_neg.score_contribution < 65

    print("OK: news_event_risk plugin sentiment scoring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python scripts/test_news_event_risk_plugin.py`
Expected: FAIL — the current plugin ignores `news_cfg` and uses flat keyword math, so
`strong_pos.score_contribution > 68` fails (today it caps positive at 65 + 5·hits).

- [ ] **Step 3: Add `news_cfg` to the engine context**

In `src/main.py`, inside the `context = { ... }` dict (around line 235), add this entry
(place it right after the `"regime": regime,` line):

```python
        "news_cfg": (configs.get("news") or {}).get("news", {}),
```

- [ ] **Step 4: Rewrite the plugin**

Replace the entire contents of `src/strategy/news_event_risk.py` with:

```python
"""NewsEventRiskStrategy — reduce/raise score using the shared sentiment scorer.

Scores each available headline with the finance-aware scorer, aggregates, and
maps polarity × confidence onto the 0-100 contribution. Low-confidence reads stay
near neutral, so a single noisy headline no longer swings the score. Negative news
weighs more heavily than positive (caution-first). Degrades to neutral with no news.
"""
from __future__ import annotations

from typing import Any, Dict, List

from news.sentiment import aggregate, score_text
from strategy.base import NEGATIVE, NEUTRAL, POSITIVE, StrategyPlugin, StrategyResult


class NewsEventRiskStrategy(StrategyPlugin):
    def name(self) -> str:
        return "news_event_risk"

    def describe(self) -> str:
        return "Finance-aware headline sentiment; confidence-damped score contribution."

    def required_fields(self) -> List[str]:
        return []  # degrades gracefully when no news is present

    def evaluate(self, symbol, market_data, portfolio_state, context) -> StrategyResult:
        headlines: List[str] = market_data.get("headlines", []) or []
        cfg = context.get("news_cfg") or {}

        if not headlines:
            return StrategyResult(
                strategy_name=self.name(),
                score_contribution=65.0,            # neutral-ish, not optimistic
                confidence=0.25,
                signal=NEUTRAL,
                reason="No headlines available; assuming no adverse news (low confidence).",
                data_used={"headlines_used": 0},
                warnings=["No news data available; using a neutral assumption."],
            )

        scores = [score_text(h, cfg) for h in headlines]
        agg = aggregate([(s.polarity, s.confidence, "yfinance", 1.0, None) for s in scores], cfg)

        ps = (cfg.get("sentiment", {}) or {}).get("plugin_scoring", {})
        neutral_base = float(ps.get("neutral_base", 65))
        max_pos = float(ps.get("max_positive", 78))
        min_neg = float(ps.get("min_negative", 25))

        effective = agg.polarity * agg.confidence       # confidence damps the deviation
        if effective >= 0:
            score = neutral_base + effective * (max_pos - neutral_base)
        else:
            score = neutral_base + effective * (neutral_base - min_neg)
        score = max(0.0, min(100.0, score))

        signal = agg.label.value  # "POSITIVE" | "NEUTRAL" | "NEGATIVE"
        risk_flags = ["news:negative_sentiment"] if signal == NEGATIVE else []

        return StrategyResult(
            strategy_name=self.name(),
            score_contribution=round(score, 1),
            confidence=max(0.2, round(agg.confidence, 2)),
            signal=signal,
            reason=(f"Scanned {len(headlines)} headline(s). Sentiment {signal} "
                    f"(polarity {agg.polarity:.2f}, confidence {agg.confidence:.2f}) "
                    f"-> {score:.0f}/100."),
            data_used={"headlines_used": len(headlines),
                       "polarity": agg.polarity,
                       "confidence": agg.confidence,
                       "negated_any": any(s.negated for s in scores)},
            warnings=[],
            risk_flags=risk_flags,
        )
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python scripts/test_news_event_risk_plugin.py`
Expected: `OK: news_event_risk plugin sentiment scoring`

- [ ] **Step 6: Run the full backend suite (no regressions)**

Run:
```bash
python scripts/test_sentiment_scorer.py && python scripts/test_news_risk_engine.py && python scripts/test_news_event_risk_plugin.py
```
Expected: three `OK:` lines.

- [ ] **Step 7: Commit**

```bash
git add src/main.py src/strategy/news_event_risk.py scripts/test_news_event_risk_plugin.py
git commit -m "feat(news): unify scoring plugin on shared confidence-damped scorer"
```

---

### Task 10 (DEFERRED — conditional on PR #9): Minimal sentiment line in `DecisionTrace.jsx`

> **Precondition:** `frontend/src/components/DecisionTrace.jsx` exists only on the
> `feature/simplified-xai-dashboard` branch (PR #9). Do NOT attempt this task on
> `feature/finance-aware-sentiment` (off `main`) — the file is absent. Apply it only
> after PR #9 merges to `main`, then rebase this branch (or do it as a follow-up PR).
> The backend (Tasks 1–9) delivers full value without this task; the new fields are
> already exported via `TradeSignal.to_dict()`.

**Files (post-merge):**
- Modify: `frontend/src/components/DecisionTrace.jsx` (the News gate cell)

- [ ] **Step 1: Surface confidence + agreement in the News gate**

In the News gate `<div className="gate">` (the one showing news risk/sentiment),
append a confidence + agreement suffix when present. Use the signal fields populated
by `apply_to_signal`: `s.news_sentiment`, `s.news_sentiment_confidence`,
`s.news_sentiment_sources_agree`. Example cell content:

```jsx
<span className="gate-label">News</span>
<span>
  {signal.news_available ? signal.news_sentiment : 'none'}
  {signal.news_available && signal.news_sentiment_confidence != null && (
    <span className="muted small">
      {` · conf ${Number(signal.news_sentiment_confidence).toFixed(2)}`}
      {signal.news_sentiment_sources_agree ? ' · 2+ sources agree' : ''}
    </span>
  )}
</span>
```

- [ ] **Step 2: Build the frontend to verify it compiles**

Run: `cd frontend && npm run build`
Expected: build succeeds (Vite reports built modules, no errors).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DecisionTrace.jsx
git commit -m "feat(ui): show news sentiment confidence + source agreement in trace"
```

---

## Self-Review

**1. Spec coverage**

| Spec section | Task |
|---|---|
| §2 shared scorer / SentimentScore | Tasks 2–5 |
| §3.1 weighted lexicon | Task 1 |
| §3.2 per-article scoring | Tasks 2–3 |
| §3.3 recency weighting | Task 3 |
| §3.4 entity relevance (proximity) | Task 3 |
| §3.5 aggregation + cross-source agreement | Task 4 |
| §4.1 overlay (hard blocks unchanged; boost scaled by confidence) | Task 8 |
| §4.2 plugin unification + confidence-damped mapping | Task 9 |
| §5 data-model + export fields | Tasks 7, 8 |
| §6 FE surfacing (deferred/conditional) | Task 10 |
| §7 config | Task 6 |
| §8 testing | Tasks 1–9 test steps |
| §9 error handling | `score_text`/`aggregate` empty-input guards (Tasks 2–4) |

**Deviation from spec §4.1 (noted to user):** the spec proposed gating
`requires_manual_review` on confidence. To honor the "never relax a caution" invariant,
the overlay does NOT relax manual-review/blocks-buy; the "not-twitchy" benefit is realized
entirely in the scoring plugin (Task 9). `manual_review_min_conf` is still loaded for
forward-use but is not applied to weaken any trigger. This is strictly more conservative
than the spec. The spec text has been amended to match.

**2. Placeholder scan:** No TBD/TODO; every code step contains complete code; every run
step has an exact command + expected output.

**3. Type consistency:** `SentimentScore(polarity, label, confidence, matched, negated, reason)`
and `AggregateSentiment(label, polarity, confidence, sources_agree, conflict, n_sources, reason)`
are used identically across Tasks 4, 8, 9. `score_text(text, cfg, *, relevance, age_hours,
company_tokens)` and `aggregate(records, cfg)` signatures match all call sites.
`aggregate` record tuple order `(polarity, confidence, provider, relevance, age_hours)` is
consistent in Tasks 4, 8, 9. New model field names match between Task 7 (definition) and
Task 8 (population).
