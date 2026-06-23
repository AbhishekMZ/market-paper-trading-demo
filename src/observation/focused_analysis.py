"""FocusedAnalysis — re-run the FULL decision stack for ONE symbol.

When a trigger needs a deeper look, we don't guess — we re-run the same engines
the deep pipeline uses (hybrid scoring -> data-quality gate -> news overlay) for
that single symbol, using fresh market data. The result says whether it is still
a valid opportunity/risk and whether paper action is allowed or blocked, and BY
WHAT. It never executes; the escalation layer does that through ExecutionEngine.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from order_models import SignalLabel


class FocusedAnalysis:
    def __init__(self, configs, provider, hybrid, news_engine, dq_engine, period="1mo", interval="1d") -> None:
        self.configs = configs
        self.provider = provider
        self.hybrid = hybrid
        self.news_engine = news_engine
        self.dq = dq_engine
        self.period = period
        self.interval = interval

    def analyze(self, symbol: str, meta: Dict[str, Any], context: Dict[str, Any],
                market_data: Optional[Dict[str, Any]] = None,
                prefetched_news: Optional[list] = None) -> Dict[str, Any]:
        # Fresh data if not supplied.
        if market_data is None:
            snap = self.provider.get_snapshot(symbol, period=self.period, interval=self.interval)
            market_data = snap.to_market_data(name=meta.get("name"), exchange=meta.get("exchange"))
            prefetched_news = list(getattr(snap, "news", []) or [])

        portfolio = context.get("portfolio", {})
        res = self.dq.assess(symbol, market_data)
        sig = self.hybrid.evaluate(symbol, market_data, portfolio, context, meta)

        # Data-quality gate (identical to the deep pipeline).
        sig.price_source = res.price_source
        sig.entry_price_used = res.entry_price_used
        sig.mtm_price_used = res.mtm_price_used
        sig.price_consistency_check = res.price_consistency_check
        sig.data_quality_verdict = res.verdict
        if res.verdict != "OK" and sig.label == SignalLabel.BUY_SMALL_PAPER:
            sig.label = SignalLabel.NO_ACTION

        # News overlay (can only add caution).
        held = symbol in context.get("held_symbols", [])
        assessment = self.news_engine.assess(symbol, sig.name, prefetched_news=prefetched_news, held=held)
        self.news_engine.apply_to_signal(sig, assessment)

        blocked_by = None
        if res.verdict != "OK":
            blocked_by = "DATA_QUALITY"
        elif sig.news_blocks_buy:
            blocked_by = "NEWS"

        result = {
            "symbol": symbol,
            "score": sig.score,
            "label": sig.label.value,
            "previous_label": meta.get("last_signal_label"),
            "valid_opportunity": sig.label == SignalLabel.BUY_SMALL_PAPER,
            "action_allowed": sig.label == SignalLabel.BUY_SMALL_PAPER,
            "manual_review": sig.label == SignalLabel.MANUAL_REVIEW,
            "blocked_by": blocked_by,
            "news_risk_level": sig.news_risk_level,
            "data_quality_verdict": sig.data_quality_verdict,
            "market_regime": sig.market_regime,
            "reason": sig.reason,
            "strengthened": (meta.get("score_when_added") is not None
                             and sig.score >= float(meta.get("score_when_added") or 0)),
        }
        return {"signal": sig, "market_data": market_data, "result": result}
