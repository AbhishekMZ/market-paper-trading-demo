"""Report generator — daily + end-of-month reports (JSON + Markdown).

Writes:
  data/reports/latest_report.json     (rich; consumed by the dashboard)
  data/reports/latest_report.md       (human-readable; used in email)
  data/reports/daily/YYYY-MM-DD.json
  data/reports/daily/YYYY-MM-DD.md
  data/reports/monthly_<YYYY-MM>.json / .md  (end of month)

It assembles state + the current run's signals/regime/executed trades into one
explainable payload. Every number is paper money.
"""
from __future__ import annotations

import os
import statistics
from typing import Any, Dict, List, Optional

import storage
from utils import money, now_ist_iso, pct, today_ist_str, month_ist_str, write_json


class ReportGenerator:
    def __init__(self, configs: Dict[str, Any]) -> None:
        self.configs = configs
        self.currency = configs["settings"].get("market", {}).get("currency_symbol", "₹")

    # ------------------------------------------------------------------ #
    # Daily
    # ------------------------------------------------------------------ #
    def build_daily(
        self,
        checkpoint: str,
        regime: Dict[str, Any],
        signals: List[Dict[str, Any]],
        executed: List[Dict[str, Any]],
        reviews: List[Dict[str, Any]],
        portfolio_summary: Dict[str, Any],
        api_usage: Dict[str, Any],
        execution_state: Dict[str, Any],
        cost_summary: Dict[str, Any],
        research_summary: Dict[str, Any],
        strategy_eval: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        buys = [s for s in signals if s["label"] == "BUY_SMALL_PAPER"]
        watch = [s for s in signals if s["label"] == "WATCH"]
        do_not_buy = [s for s in signals if s["label"] in ("DO_NOT_BUY", "HIGH_RISK_IGNORE")]
        manual = [s for s in signals if s["label"] == "MANUAL_REVIEW"]
        no_trade = [
            {"symbol": s["symbol"], "label": s["label"], "score": s["score"], "reason": s["reason"]}
            for s in signals
            if s["label"] in ("NO_ACTION", "HOLD", "WATCH", "DO_NOT_BUY", "HIGH_RISK_IGNORE", "MANUAL_REVIEW")
        ]
        data_warnings = sorted({w for s in signals for w in s.get("warnings", [])})
        conflicts = [f"{s['symbol']}: {c}" for s in signals for c in s.get("conflict_warnings", [])]
        strategy_summary = self._strategy_summary(signals)

        payload = {
            "generated_at": now_ist_iso(),
            "date": today_ist_str(),
            "checkpoint": checkpoint,
            "mode_banner": "PAPER TRADING ONLY — fake money. Live trading is DISABLED.",
            "execution": {
                "mode": execution_state.get("mode", "paper"),
                "broker_adapter": execution_state.get("broker_adapter", "paper"),
                "live_trading_enabled": execution_state.get("live_trading_enabled", False),
                "angel_one_enabled": execution_state.get("angel_one_enabled", False),
                "require_manual_approval": execution_state.get("require_manual_approval", True),
                "allow_real_orders": execution_state.get("allow_real_orders", False),
                "kill_switch": execution_state.get("kill_switch", False),
            },
            "market_regime": regime,
            "portfolio": portfolio_summary,
            "cost_adjusted_pnl": cost_summary,
            "top_candidates": buys,
            "watchlist": watch,
            "do_not_buy": do_not_buy,
            "manual_review": manual,
            "executed_trades": executed,
            "positions_under_review": reviews,
            "no_trade_reasons": no_trade,
            "strategy_summary": strategy_summary,
            "conflicts": conflicts,
            "signals": signals,
            "api_usage": api_usage,
            "data_quality_warnings": data_warnings,
            "research": research_summary,
            "strategy_evaluation": strategy_eval or {},
            "future_readiness": self._future_readiness(execution_state, research_summary),
        }
        return payload

    def write_daily(self, payload: Dict[str, Any]) -> None:
        storage.ensure_dirs()
        write_json(os.path.join(storage.REPORTS_DIR, "latest_report.json"), payload)
        write_json(os.path.join(storage.DAILY_REPORTS_DIR, f"{payload['date']}.json"), payload)
        md = self.render_markdown(payload)
        with open(os.path.join(storage.REPORTS_DIR, "latest_report.md"), "w", encoding="utf-8") as fh:
            fh.write(md)
        with open(os.path.join(storage.DAILY_REPORTS_DIR, f"{payload['date']}.md"), "w", encoding="utf-8") as fh:
            fh.write(md)

    # ------------------------------------------------------------------ #
    # Warning report (e.g. budget exhausted / no data)
    # ------------------------------------------------------------------ #
    def write_warning(self, checkpoint: str, message: str, api_usage: Dict[str, Any]) -> Dict[str, Any]:
        storage.ensure_dirs()
        payload = {
            "generated_at": now_ist_iso(),
            "date": today_ist_str(),
            "checkpoint": checkpoint,
            "mode_banner": "PAPER TRADING ONLY — fake money. Live trading is DISABLED.",
            "warning": message,
            "api_usage": api_usage,
        }
        write_json(os.path.join(storage.REPORTS_DIR, "latest_report.json"), payload)
        with open(os.path.join(storage.REPORTS_DIR, "latest_report.md"), "w", encoding="utf-8") as fh:
            fh.write(f"# Paper Trading — Warning\n\n_{payload['generated_at']}_\n\n> {message}\n")
        return payload

    # ------------------------------------------------------------------ #
    # Monthly
    # ------------------------------------------------------------------ #
    def build_monthly(
        self, portfolio_summary: Dict[str, Any], cost_summary: Dict[str, Any],
        strategy_eval: Dict[str, Any], benchmark_return_pct: Optional[float],
        research_summary: Dict[str, Any], execution_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        trades = storage.load_state("trade_history", [])
        closed = portfolio_summary.get("closed", [])
        realized = [float(c.get("realized_pnl", 0.0)) for c in closed]
        wins = [r for r in realized if r >= 0]
        losses = [r for r in realized if r < 0]
        ready, ready_reasons = self._manual_approval_readiness(portfolio_summary, strategy_eval, closed)

        return {
            "generated_at": now_ist_iso(),
            "month": month_ist_str(),
            "mode_banner": "PAPER TRADING ONLY — fake money. Live trading is DISABLED.",
            "fake_pnl": portfolio_summary.get("total_pnl", 0.0),
            "cost_adjusted_pnl": cost_summary,
            "total_return_pct": portfolio_summary.get("total_return_pct", 0.0),
            "benchmark_return_pct": benchmark_return_pct,
            "beat_benchmark": (
                None if benchmark_return_pct is None
                else portfolio_summary.get("total_return_pct", 0.0) > benchmark_return_pct
            ),
            "num_trades": len([t for t in trades if t.get("status") == "FILLED"]) if isinstance(trades, list) else 0,
            "closed_trades": len(closed),
            "win_rate_pct": round(len(wins) / len(closed) * 100, 1) if closed else 0.0,
            "average_gain": round(statistics.fmean(wins), 2) if wins else 0.0,
            "average_loss": round(statistics.fmean(losses), 2) if losses else 0.0,
            "max_drawdown_pct": portfolio_summary.get("max_drawdown_pct", 0.0),
            "best_trade": max(realized, default=0.0),
            "worst_trade": min(realized, default=0.0),
            "strategy_evaluation": strategy_eval,
            "research": research_summary,
            "manual_approval_ready": ready,
            "manual_approval_reasons": ready_reasons,
            "recommendation": self._recommendation(ready, portfolio_summary, closed),
        }

    def write_monthly(self, payload: Dict[str, Any]) -> None:
        storage.ensure_dirs()
        base = os.path.join(storage.REPORTS_DIR, f"monthly_{payload['month']}")
        write_json(base + ".json", payload)
        with open(base + ".md", "w", encoding="utf-8") as fh:
            fh.write(self.render_monthly_markdown(payload))

    # ------------------------------------------------------------------ #
    # Markdown rendering
    # ------------------------------------------------------------------ #
    def render_markdown(self, p: Dict[str, Any]) -> str:
        pf = p["portfolio"]
        rg = p["market_regime"]
        L: List[str] = []
        L.append(f"# 📄 Paper Trading Report — {p['date']} ({p['checkpoint']})")
        L.append("")
        L.append(f"> **{p['mode_banner']}**")
        L.append("")
        L.append(f"**Market regime:** `{rg.get('regime','?')}` — {rg.get('reason','')}")
        L.append("")
        L.append("## 💰 Portfolio (fake money)")
        L.append(f"- Total value: **{money(pf.get('total_value',0), self.currency)}** "
                 f"(started {money(pf.get('starting_capital',0), self.currency)})")
        L.append(f"- Cash: {money(pf.get('cash',0), self.currency)} · Holdings: {money(pf.get('holdings_value',0), self.currency)}")
        L.append(f"- Realized P&L: {money(pf.get('realized_pnl',0), self.currency)} · "
                 f"Unrealized: {money(pf.get('unrealized_pnl',0), self.currency)}")
        L.append(f"- Total return: {pct(pf.get('total_return_pct',0))} · Max drawdown: {pct(pf.get('max_drawdown_pct',0))}")
        L.append(f"- Monthly budget: deployed {money(pf.get('capital_deployed',0), self.currency)} / "
                 f"{money(pf.get('monthly_capital',0), self.currency)} · "
                 f"buys {pf.get('buys_this_month',0)}/{pf.get('max_buys_per_month',5)}")
        cap = p.get("cost_adjusted_pnl", {})
        if cap:
            L.append(f"- **Cost-adjusted** net realized: {money(cap.get('net_realized_pnl_cost_adjusted',0), self.currency)} "
                     f"(est. costs {money(cap.get('estimated_costs',0), self.currency)})")
        L.append("")

        L.append("## ✅ Top paper-buy candidates")
        if p["top_candidates"]:
            for s in p["top_candidates"]:
                L.append(f"- **{s['symbol']}** score {s['score']} ({s['risk_level']} risk) — {s['reason']}")
        else:
            L.append("- None this checkpoint.")
        L.append("")

        if p["executed_trades"]:
            L.append("## 🧾 Paper trades executed this run")
            for t in p["executed_trades"]:
                L.append(f"- {t.get('side')} {t.get('symbol')} x{t.get('quantity')} @ "
                         f"{money(t.get('price',0), self.currency)} → {t.get('status')} ({t.get('message','')})")
            L.append("")

        if p["positions_under_review"]:
            L.append("## ⚠️ Positions under review (no auto-sell)")
            for r in p["positions_under_review"]:
                L.append(f"- {r['symbol']}: {pct(r['unrealized_pnl_pct'])} → {r['label']} ({r['reason']})")
            L.append("")

        L.append("## 👀 Watchlist")
        L.append(", ".join(f"{s['symbol']}({s['score']})" for s in p["watchlist"]) or "None.")
        L.append("")
        L.append("## 🚫 Do-not-buy")
        L.append(", ".join(f"{s['symbol']}({s['score']})" for s in p["do_not_buy"]) or "None.")
        L.append("")

        L.append("## 🧠 Strategy contribution summary")
        for name, info in p["strategy_summary"].items():
            tag = "" if info["contributes"] else " _(display-only)_"
            L.append(f"- {name}{tag}: avg {info['avg_score']:.0f}/100 (weight {info['weight']})")
        L.append("")

        if p["conflicts"]:
            L.append("## ❗ Strategy conflicts")
            for c in p["conflicts"]:
                L.append(f"- {c}")
            L.append("")

        L.append("## 🤔 Why no trade (selected)")
        for nt in p["no_trade_reasons"][:8]:
            L.append(f"- {nt['symbol']} ({nt['label']}, {nt['score']}): {nt['reason']}")
        L.append("")

        au = p["api_usage"]
        L.append("## 📊 Market-data usage")
        L.append(f"- Provider: `{au.get('provider','?')}` · calls today: "
                 f"{au.get('calls_today', au.get('daily',{}).get(p['date'],0))} · "
                 f"total this month: {au.get('calls_total',0)} (no API-key quota)")
        L.append("")
        if p["data_quality_warnings"]:
            L.append("## 🧪 Data-quality warnings")
            for w in p["data_quality_warnings"]:
                L.append(f"- {w}")
            L.append("")

        L.append("## 🔭 Future-readiness checklist")
        for item in p["future_readiness"]:
            mark = "✅" if item["done"] else "⬜"
            L.append(f"- {mark} {item['item']}")
        L.append("")
        L.append("---")
        L.append("_This is a fake-money paper-trading demo. No real orders were placed. Not investment advice._")
        return "\n".join(L)

    def render_monthly_markdown(self, p: Dict[str, Any]) -> str:
        L = [f"# 📅 End-of-Month Paper Report — {p['month']}", "",
             f"> **{p['mode_banner']}**", "",
             "## Results (fake money)",
             f"- Fake P&L: {money(p['fake_pnl'], self.currency)} · Return: {pct(p['total_return_pct'])}",
             f"- Cost-adjusted net realized: {money(p['cost_adjusted_pnl'].get('net_realized_pnl_cost_adjusted',0), self.currency)}",
             f"- NIFTY benchmark return: {pct(p['benchmark_return_pct']) if p['benchmark_return_pct'] is not None else 'n/a'}"
             f" · Beat benchmark: {p['beat_benchmark']}",
             f"- Trades: {p['num_trades']} · Closed: {p['closed_trades']} · Win rate: {p['win_rate_pct']}%",
             f"- Avg gain: {money(p['average_gain'], self.currency)} · Avg loss: {money(p['average_loss'], self.currency)}",
             f"- Max drawdown: {pct(p['max_drawdown_pct'])} · Best: {money(p['best_trade'], self.currency)} · "
             f"Worst: {money(p['worst_trade'], self.currency)}", "",
             "## Manual-approval readiness",
             f"- Ready for manual-approval real trading? **{p['manual_approval_ready']}**"]
        for r in p["manual_approval_reasons"]:
            L.append(f"  - {r}")
        L.append("")
        L.append(f"## Recommendation\n\n**{p['recommendation']}**")
        L.append("")
        L.append("_Do not over-trust one month of data. See docs/strategy_validation_principles.md._")
        return "\n".join(L)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _strategy_summary(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        weights = self.configs["scoring"].get("hybrid_scoring", {}).get("weights", {})
        agg: Dict[str, Dict[str, Any]] = {}
        for s in signals:
            for r in s.get("strategy_results", []):
                name = r["strategy_name"]
                a = agg.setdefault(name, {"scores": [], "contributes": r.get("contributes_to_score", False)})
                a["scores"].append(r.get("score_contribution", 0))
        out = {}
        for name, a in agg.items():
            out[name] = {
                "avg_score": round(statistics.fmean(a["scores"]), 1) if a["scores"] else 0.0,
                "weight": weights.get(name, 0),
                "contributes": bool(a["contributes"]),
            }
        return out

    def _future_readiness(self, execution_state: Dict[str, Any], research: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {"item": "Phase 1: Paper trading running (email + GitHub Pages, ₹0 cost)", "done": True},
            {"item": "BrokerAdapter abstraction in place (paper enabled, Angel One stub disabled)", "done": True},
            {"item": "Live trading disabled by config", "done": not execution_state.get("live_trading_enabled", False)},
            {"item": "Angel One adapter disabled by config", "done": not execution_state.get("angel_one_enabled", False)},
            {"item": "Manual approval required for any real order", "done": execution_state.get("require_manual_approval", True)},
            {"item": "≥1 strategy accepted for manual review (post-validation)", "done": bool(research.get("real_trading_eligible"))},
            {"item": "Phase 2: Manual-approval real trading (future)", "done": False},
            {"item": "Phase 3: Limited real execution, delivery+limit only (future)", "done": False},
            {"item": "Phase 4: Controlled automation w/ kill switch (future)", "done": False},
        ]

    def _manual_approval_readiness(self, pf, strategy_eval, closed) -> tuple[bool, List[str]]:
        reasons = []
        enough_trades = len(closed) >= 5
        reasons.append(f"Closed paper trades ≥ 5: {enough_trades} ({len(closed)}).")
        dd_ok = pf.get("max_drawdown_pct", 0.0) > -20
        reasons.append(f"Max drawdown better than -20%: {dd_ok} ({pf.get('max_drawdown_pct',0):.1f}%).")
        positive = pf.get("total_pnl", 0.0) > 0
        reasons.append(f"Net paper P&L positive: {positive}.")
        ready = enough_trades and dd_ok and positive
        reasons.append("NOTE: readiness is necessary-but-not-sufficient; out-of-sample validation still required.")
        return ready, reasons

    def _recommendation(self, ready: bool, pf, closed) -> str:
        if len(closed) < 5:
            return "Continue paper trading — not enough closed trades to judge."
        if ready:
            return "Consider MANUAL-APPROVAL mode next (still no automation). Validate out-of-sample first."
        return "Continue paper trading / review strategy — readiness criteria not met."
