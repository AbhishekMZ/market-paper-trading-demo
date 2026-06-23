"""NewsRiskEngine — post-strategy RISK overlay.

Pipeline per symbol:
  fetch (yfinance snapshot news + GDELT) -> normalize -> dedupe -> per-item
  relevance / sentiment / event-classification -> aggregate -> verdict.

Cardinal rules (enforced here, not just documented):
  * News can only ADD caution. `apply_to_signal` may DOWNGRADE a buy
    (WATCH / MANUAL_REVIEW / NO_ACTION) but can NEVER create or upgrade one.
  * Positive news is recorded as an informational `sentiment_boost` and is NOT
    added to the score — the scoring layer's `news_event_risk` plugin already
    grants a small positive nudge, so the overlay stays purely protective.
  * Every failure path degrades to "no news" (safe), never raises.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from news.base import (
    NewsItem,
    NewsRiskAssessment,
    NewsRiskLevel,
    NewsSentiment,
    max_risk,
    risk_rank,
)
from news.cache import NewsCache
from news.deduper import dedupe
from news.event_classifier import classify_events
from news.providers import build_news_providers
from news.relevance import relevance_score
from news.sentiment import aggregate_sentiment, classify_sentiment
from order_models import SignalLabel
from utils import now_ist_iso


class NewsRiskEngine:
    def __init__(self, news_cfg: Dict[str, Any]) -> None:
        cfg = news_cfg or {}
        # Tolerate being handed the whole news.yml mapping ({"news": {...}}) as
        # well as the inner block, so a call-site nesting slip can't silently
        # drop the config and fall back to code defaults.
        if isinstance(cfg.get("news"), dict):
            cfg = cfg["news"]
        self.cfg = cfg
        self.enabled = bool(cfg.get("enabled", True))
        self.cache = NewsCache(cfg)
        self.providers = build_news_providers(cfg, cache=self.cache)

        rel = cfg.get("relevance", {})
        self.min_relevance = float(rel.get("min_score", 0.3))
        self.require_rel_for_gdelt = bool(rel.get("require_relevance_for_gdelt", True))
        self.keep_yf_unfiltered = bool(rel.get("keep_yfinance_unfiltered", True))

        block = cfg.get("blocking", {})
        self.high_blocks_buy = bool(block.get("high_risk_news_blocks_buy", True))
        self.critical_exit_review = bool(block.get("critical_news_triggers_exit_review", True))
        self.medium_manual_review = bool(block.get("medium_risk_news_triggers_manual_review", True))

        self.boost_cap = float(cfg.get("scoring", {}).get("positive_sentiment_boost_max", 3.0))
        self.max_age_hours = float(cfg.get("freshness", {}).get("max_age_hours", 96))

        alert = cfg.get("alerting", {})
        self.alert_send_on = alert.get("send_on", {})
        self.max_alerts_per_run = int(alert.get("max_alerts_per_run", 5))

    # ------------------------------------------------------------------ #
    def assess(
        self,
        symbol: str,
        company_name: Optional[str] = None,
        prefetched_news: Optional[List[Dict[str, Any]]] = None,
        held: bool = False,
    ) -> NewsRiskAssessment:
        if not self.enabled:
            return NewsRiskAssessment(symbol=symbol, company_name=company_name, assessed_at=now_ist_iso())

        items = self._gather(symbol, company_name, prefetched_news)
        items = dedupe(items)
        for it in items:
            self._enrich(it, symbol, company_name)
        kept = [it for it in items if self._is_relevant(it)]

        # Only reasonably-fresh items influence the verdict; older = context only.
        blocking_pool = [it for it in kept if (it.age_hours is None or it.age_hours <= self.max_age_hours)]

        worst = NewsRiskLevel.NONE
        for it in blocking_pool:
            worst = max_risk(worst, it.risk_level)
        overall_sentiment = aggregate_sentiment([it.sentiment for it in blocking_pool])
        event_types = sorted({t for it in blocking_pool for t in it.event_types})
        fresh_count = sum(1 for it in kept if it.is_fresh)

        blocks_buy = self.high_blocks_buy and risk_rank(worst) >= risk_rank(NewsRiskLevel.HIGH)
        manual_review = (
            self.medium_manual_review and worst == NewsRiskLevel.MEDIUM
            and overall_sentiment == NewsSentiment.NEGATIVE
        )
        exit_review = self.critical_exit_review and held and worst == NewsRiskLevel.CRITICAL

        boost = 0.0
        if not blocks_buy and overall_sentiment == NewsSentiment.POSITIVE and worst == NewsRiskLevel.NONE:
            boost = min(self.boost_cap, 1.0 + 0.5 * fresh_count)

        reasons = self._reasons(kept, worst, overall_sentiment, blocks_buy, manual_review, exit_review)
        ranked = sorted(kept, key=lambda i: (-risk_rank(i.risk_level), i.age_hours if i.age_hours is not None else 48.0))

        return NewsRiskAssessment(
            symbol=symbol,
            company_name=company_name,
            news_available=bool(kept),
            item_count=len(kept),
            fresh_item_count=fresh_count,
            overall_sentiment=overall_sentiment,
            news_risk_level=worst,
            dominant_event_types=event_types,
            blocks_buy=blocks_buy,
            requires_manual_review=manual_review,
            exit_review_for_holding=exit_review,
            sentiment_boost=round(boost, 2),
            reasons=reasons,
            providers_used=sorted({it.provider for it in kept}),
            top_items=[i.to_dict() for i in ranked[:5]],
            critical_items=[i.to_dict() for i in ranked if risk_rank(i.risk_level) >= risk_rank(NewsRiskLevel.HIGH)][:5],
            assessed_at=now_ist_iso(),
        )

    # ------------------------------------------------------------------ #
    def apply_to_signal(self, signal, assessment: NewsRiskAssessment) -> None:
        """Attach news provenance to the signal and downgrade buys on risk.

        NEVER upgrades a label. The score is left untouched (see module docstring).
        """
        signal.news_available = assessment.news_available
        signal.news_risk_level = assessment.news_risk_level.value
        signal.news_sentiment = assessment.overall_sentiment.value
        signal.news_event_types = list(assessment.dominant_event_types)
        signal.news_item_count = assessment.item_count
        signal.news_blocks_buy = assessment.blocks_buy
        signal.news_reasons = list(assessment.reasons)
        if assessment.top_items:
            signal.news_top_headline = assessment.top_items[0].get("title")

        if signal.label != SignalLabel.BUY_SMALL_PAPER:
            # Overlay never turns a non-buy into a buy. Still flag exit reviews.
            if assessment.exit_review_for_holding and signal.label in (SignalLabel.HOLD, SignalLabel.WATCH):
                signal.label = SignalLabel.EXIT_REVIEW
                signal.warnings = list(signal.warnings) + ["News:CRITICAL on holding -> EXIT_REVIEW."]
            return

        if assessment.blocks_buy:
            new_label = (
                SignalLabel.NO_ACTION
                if assessment.news_risk_level == NewsRiskLevel.CRITICAL
                else SignalLabel.WATCH
            )
            signal.label = new_label
            signal.warnings = list(signal.warnings) + [
                f"News:{assessment.news_risk_level.value} adverse -> buy blocked (downgraded to {new_label.value})."
            ]
            signal.reason = f"[NEWS {assessment.news_risk_level.value}] " + signal.reason
        elif assessment.requires_manual_review:
            signal.label = SignalLabel.MANUAL_REVIEW
            signal.warnings = list(signal.warnings) + ["News:MEDIUM adverse -> manual review before any buy."]
            signal.reason = "[NEWS MEDIUM] " + signal.reason

    # ------------------------------------------------------------------ #
    def build_alert(self, assessment: NewsRiskAssessment, was_buy_candidate: bool = False,
                    held: bool = False) -> Optional[Dict[str, Any]]:
        """Return an email payload dict if this assessment warrants alerting, else None."""
        lvl = assessment.news_risk_level
        send_on = self.alert_send_on
        fire = False
        if lvl == NewsRiskLevel.CRITICAL and send_on.get("critical_news", True):
            fire = True
        if lvl == NewsRiskLevel.HIGH and held and send_on.get("high_risk_news_on_position", True):
            fire = True
        if assessment.blocks_buy and was_buy_candidate and send_on.get("high_risk_news_blocked_buy", True):
            fire = True
        if not fire:
            return None

        head = assessment.top_items[0].get("title") if assessment.top_items else "(no headline)"
        sym = assessment.symbol
        subject = f"[Paper News] {lvl.value} news: {sym}"
        body = "\n".join([
            f"Symbol: {sym} ({assessment.company_name or ''})",
            f"News risk: {lvl.value}   Sentiment: {assessment.overall_sentiment.value}",
            f"Events: {', '.join(assessment.dominant_event_types) or 'none'}",
            f"Held position: {'yes' if held else 'no'}   Blocked a would-be buy: {'yes' if (assessment.blocks_buy and was_buy_candidate) else 'no'}",
            f"Top headline: {head}",
            "",
            "Why: " + ("; ".join(assessment.reasons) or "n/a"),
            "",
            "Reminder: PAPER TRADING ONLY. No real order was placed. News never triggers a buy — it can only block one.",
        ])
        return {"key": f"{sym}:{lvl.value}", "subject": subject, "body": body, "symbol": sym, "level": lvl.value}

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _gather(self, symbol, company_name, prefetched_news) -> List[NewsItem]:
        out: List[NewsItem] = []
        for p in self.providers:
            try:
                pre = prefetched_news if p.name == "yfinance" else None
                out.extend(p.fetch(symbol, company_name, prefetched=pre))
            except Exception:
                continue  # a single provider must never break the run
        return out

    def _enrich(self, item: NewsItem, symbol, company_name) -> None:
        text = f"{item.title} {item.summary}".strip()
        item.relevance = (
            1.0 if item.provider == "yfinance" else relevance_score(text, symbol, company_name)
        )
        sentiment, neg, pos = classify_sentiment(text, self.cfg)
        item.sentiment = sentiment
        types, risk, matched = classify_events(text, self.cfg)
        item.event_types = types
        item.risk_level = risk
        item.matched_keywords = sorted(set(neg + pos + matched))

    def _is_relevant(self, item: NewsItem) -> bool:
        if item.provider == "yfinance" and self.keep_yf_unfiltered:
            return True
        if item.provider == "gdelt" and not self.require_rel_for_gdelt:
            return True
        return item.relevance >= self.min_relevance

    def _reasons(self, items, worst, sentiment, blocks_buy, manual_review, exit_review) -> List[str]:
        reasons: List[str] = []
        if not items:
            reasons.append("No relevant news found (treated as neutral).")
            return reasons
        reasons.append(f"{len(items)} relevant item(s); worst risk {worst.value}, sentiment {sentiment.value}.")
        flagged = [i for i in items if risk_rank(i.risk_level) >= risk_rank(NewsRiskLevel.MEDIUM)]
        for i in flagged[:3]:
            reasons.append(f"[{i.risk_level.value}] {i.title[:120]}")
        if blocks_buy:
            reasons.append("HIGH/CRITICAL adverse news -> new paper buy blocked.")
        if exit_review:
            reasons.append("CRITICAL news on a held position -> EXIT_REVIEW (advisory; never auto-sells).")
        if manual_review:
            reasons.append("MEDIUM adverse news -> manual review before any buy.")
        return reasons
