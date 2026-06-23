"""main.py — paper-trading analyzer entry point.

Run examples (from repo root):
    python src/main.py --checkpoint auto      # infer checkpoint from IST time
    python src/main.py --checkpoint open      # force the 09:35 checkpoint
    python src/main.py --manual               # manual one-off run
    python src/main.py --eod                  # treat as end-of-day (send email)
    python src/main.py --monthly              # also produce the month report

Market data comes from a swappable MarketDataProvider (v1: Yahoo Finance via the
UNOFFICIAL yfinance library — no API key). SAFETY: v1 is paper-trading only; the
execution engine refuses to run on any unsafe configuration.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure sibling modules import cleanly whether run as a script or module.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Optionally load a local .env (no-op in CI, where secrets are injected).
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

import static_exporter  # noqa: E402
import storage  # noqa: E402
from backtesting.cost_model import CostModel  # noqa: E402
from backtesting.backtest_engine import PaperTradeReplay  # noqa: E402
from broker import build_adapter  # noqa: E402
from data_quality import DataQualityEngine  # noqa: E402
from email_sender import EmailSender  # noqa: E402
from execution_engine import ExecutionEngine, ExecutionHaltError  # noqa: E402
from market_data import build_market_data_provider  # noqa: E402
from order_models import SignalLabel  # noqa: E402
from portfolio_manager import PortfolioManager  # noqa: E402
from report_generator import ReportGenerator  # noqa: E402
from risk_engine import RiskEngine  # noqa: E402
from scheduler import is_trading_day, resolve_checkpoint  # noqa: E402
from strategy.hybrid_signal_engine import HybridSignalEngine  # noqa: E402
from strategy.market_regime import MarketRegimeEngine  # noqa: E402
from strategy.research_registry import ResearchRegistry  # noqa: E402
from strategy.strategy_evaluator import StrategyEvaluator  # noqa: E402
from universe_loader import load_universe  # noqa: E402
from utils import month_ist_str, now_ist_iso, today_ist_str  # noqa: E402


class UsageTracker:
    """Lightweight provider-usage stats (no hard budget — yfinance has no quota)."""

    def __init__(self, provider_name: str) -> None:
        u = storage.load_state("api_usage", {})
        if not u or u.get("month") != month_ist_str():
            u = {"month": month_ist_str(), "calls_total": 0, "daily": {}, "warnings": []}
        u["provider"] = provider_name
        u["budget_enabled"] = False
        u["note"] = "yfinance has no API key/quota; polite limits applied."
        u.setdefault("daily", {})
        u.setdefault("warnings", [])
        self.u = u

    def record(self, n: int = 1) -> None:
        today = today_ist_str()
        self.u["calls_total"] = int(self.u.get("calls_total", 0)) + n
        self.u["daily"][today] = int(self.u["daily"].get(today, 0)) + n

    def calls_today(self) -> int:
        return int(self.u["daily"].get(today_ist_str(), 0))

    def warn(self, message: str) -> None:
        self.u["warnings"].append({"ts": now_ist_iso(), "message": message})

    def save(self) -> Dict[str, Any]:
        self.u["calls_today"] = self.calls_today()
        self.u["last_updated"] = now_ist_iso()
        storage.save_state("api_usage", self.u)
        return self.u


def fetch_benchmarks(provider, configs, usage, period, interval) -> Tuple[Dict[str, Any], Optional[float]]:
    """Fetch benchmark indices for the regime engine. Returns (data, primary_change_pct)."""
    bench_cfg = configs["universe"].get("benchmarks", {})
    if not bench_cfg.get("fetch_regime", True):
        return {}, None
    out: Dict[str, Any] = {}
    primary_change = None
    primary = bench_cfg.get("primary")
    if primary:
        snap = provider.get_snapshot(primary["symbol"], period=period, interval=interval)
        usage.record()
        md = snap.to_market_data(name=primary.get("name"), exchange=primary.get("exchange"))
        out[primary.get("name", primary["symbol"])] = md
        if md.get("ok"):
            primary_change = md.get("change_pct")
    for sec in bench_cfg.get("secondary", []) or []:
        snap = provider.get_snapshot(sec["symbol"], period=period, interval=interval)
        usage.record()
        out[sec.get("name", sec["symbol"])] = snap.to_market_data(name=sec.get("name"), exchange=sec.get("exchange"))
    return out, primary_change


def run(args: argparse.Namespace) -> int:
    storage.ensure_dirs()
    configs = storage.load_all_configs()
    settings = configs["settings"]
    capital = settings.get("capital", {})
    md_cfg = settings.get("market_data", {})
    period = md_cfg.get("period", "1mo")
    interval = md_cfg.get("interval", "1d")

    # --- build components (paper adapter is the only enabled adapter) ---- #
    risk = RiskEngine(configs["risk"])
    pm = PortfolioManager(settings)
    cost_model = CostModel(configs["costs"])
    adapter = build_adapter(
        configs["broker"].get("broker", {}).get("active_adapter", "paper"),
        starting_capital=float(capital.get("monthly_fake_capital", 10000)),
        max_trade_amount=float(capital.get("max_amount_per_trade", 2000)),
    )
    engine = ExecutionEngine(configs, adapter, risk, pm)
    report = ReportGenerator(configs)

    # --- SAFETY GATE: refuse to run on unsafe configuration -------------- #
    try:
        for note in engine.validate_safety():
            print(f"[safety] {note}")
    except ExecutionHaltError as exc:
        print(f"[HALT] {exc}", file=sys.stderr)
        storage.append_audit({"event": "EXECUTION_HALTED", "message": str(exc)})
        return 2

    exec_state = engine.load_state()
    checkpoint = resolve_checkpoint(settings, args.checkpoint)
    cp_id = checkpoint["id"]
    print(f"[run] checkpoint={cp_id} last={checkpoint['is_last']} day={today_ist_str()}")

    usage = UsageTracker(md_cfg.get("provider", "yfinance"))

    if exec_state.get("kill_switch"):
        report.write_warning(cp_id, "Kill switch is ON — no analysis or trades performed.", usage.save())
        static_exporter.export_all()
        return 0

    if not is_trading_day(settings) and not (args.manual or args.force):
        report.write_warning(cp_id, "Not a weekday trading day — skipping scan.", usage.save())
        static_exporter.export_all()
        return 0

    try:
        provider = build_market_data_provider(md_cfg.get("provider", "yfinance"), settings.get("rate_limits", {}))
    except Exception as exc:
        report.write_warning(cp_id, f"Market-data provider error: {exc}", usage.save())
        static_exporter.export_all()
        return 1

    # --- market regime --------------------------------------------------- #
    benchmarks, bench_change = fetch_benchmarks(provider, configs, usage, period, interval)
    regime = MarketRegimeEngine().classify(benchmarks)
    print(f"[regime] {regime.regime} (score {regime.score}) — {regime.reason}")

    # --- market data for the active universe ----------------------------- #
    max_symbols = int(md_cfg.get("max_symbols_per_run", 10))
    universe = load_universe(max_active=max_symbols)
    dq = DataQualityEngine(settings.get("data_quality", {}))
    market_by_symbol: Dict[str, Tuple[Dict[str, Any], Dict[str, str]]] = {}
    prices: Dict[str, float] = {}
    dq_results = []
    dq_by_symbol: Dict[str, Any] = {}
    incidents: List[Dict[str, Any]] = []
    anomalous_symbols = set()
    for meta in universe["active"]:
        snap = provider.get_snapshot(meta["symbol"], period=period, interval=interval)
        usage.record()
        md = snap.to_market_data(name=meta.get("name"), exchange=meta.get("exchange"))
        market_by_symbol[meta["symbol"]] = (md, meta)
        # Data-quality gate: assess BEFORE the price is trusted.
        res = dq.assess(meta["symbol"], md)
        dq_results.append(res)
        dq_by_symbol[meta["symbol"]] = res
        inc = dq.incident(res)
        if inc:
            incidents.append(inc)
        if res.verdict == "DATA_ANOMALY":
            anomalous_symbols.add(meta["symbol"])
        # Only trust the price for marking/sizing when it passed the gate.
        if md.get("price") and res.verdict == "OK":
            prices[meta["symbol"]] = md["price"]

    adapter.set_prices(prices)
    mtm_jump = float(settings.get("data_quality", {}).get("mtm_jump_pct", 15))
    pm.mark_to_market(prices, anomalous_symbols=anomalous_symbols, mtm_jump_pct=mtm_jump)
    incidents.extend(getattr(pm, "last_mtm_incidents", []))
    portfolio = storage.load_state("portfolio", {})
    held = [p["symbol"] for p in portfolio.get("positions", [])]
    budget = pm.load_budget()

    hybrid = HybridSignalEngine(configs, cost_model=cost_model)
    research = ResearchRegistry()
    context = {
        "regime": regime,
        "benchmark_change_pct": bench_change if bench_change is not None else regime.inputs.get("avg_change_pct"),
        "held_symbols": held,
        "budget": budget,
        "limits": {
            "max_trade_amount": float(capital.get("max_amount_per_trade", 2000)),
            "max_buys_per_day": int(capital.get("max_buys_per_day", 1)),
            "max_buys_per_month": int(capital.get("max_buys_per_month", 5)),
        },
        "buys_today": exec_state.get("buys_today", 0),
        "checkpoint": cp_id,
    }

    # --- evaluate every symbol (engine receives normalized market data) -- #
    signals = []
    for symbol, (md, meta) in market_by_symbol.items():
        sig = hybrid.evaluate(symbol, md, portfolio, context, meta)
        # Attach data-quality provenance and enforce the gate on the signal.
        res = dq_by_symbol.get(symbol)
        if res is not None:
            sig.price_source = res.price_source
            sig.entry_price_used = res.entry_price_used
            sig.mtm_price_used = res.mtm_price_used
            sig.price_consistency_check = res.price_consistency_check
            sig.data_quality_verdict = res.verdict
            if res.verdict != "OK":
                if sig.label == SignalLabel.BUY_SMALL_PAPER:
                    sig.label = SignalLabel.NO_ACTION
                sig.warnings = list(sig.warnings) + [f"DataQuality:{res.verdict}"] + res.reasons[:2]
                sig.reason = f"[DATA {res.verdict}] " + sig.reason
        signals.append(sig)
    signals.sort(key=lambda s: s.score, reverse=True)
    dq.save_source_log()

    # --- process paper buys (risk engine enforces all hard limits) ------- #
    executed: List[Dict[str, Any]] = []
    max_trade = float(capital.get("max_amount_per_trade", 2000))
    for sig in signals:
        if sig.label != SignalLabel.BUY_SMALL_PAPER:
            continue
        result = engine.process_buy(sig, amount_cap=max_trade, prices=prices, checkpoint=cp_id)
        if result is not None:
            executed.append(result.to_dict())
            if result.status.value == "FILLED":
                sig.led_to_paper_trade = True

    # Re-value the portfolio after any fills so holdings/total/unrealized are current.
    pm.mark_to_market(prices, anomalous_symbols=anomalous_symbols, mtm_jump_pct=mtm_jump)

    # --- audit each signal (comprehensive entry) ------------------------- #
    for sig in signals:
        _audit_signal(sig, regime, adapter, engine)
    _persist_signal_history(signals)

    # --- loss reviews (advisory; never auto-sell) ------------------------ #
    portfolio = storage.load_state("portfolio", {})
    reviews = risk.review_positions(portfolio)
    storage.save_state("portfolio", portfolio)

    # --- evaluation + cost replay + summaries ---------------------------- #
    strat_eval = StrategyEvaluator().evaluate()
    replay = PaperTradeReplay(cost_model).summarize()
    research_summary = research.summary()
    pf_summary = pm.summary()
    exec_state = engine.load_state()

    if not any(s.data_quality.value in ("GOOD", "ACCEPTABLE") for s in signals):
        usage.warn("No usable market data this run (provider returned nothing usable); declined to trade.")

    payload = report.build_daily(
        checkpoint=cp_id,
        regime=regime.to_dict(),
        signals=[s.to_dict() for s in signals],
        executed=executed,
        reviews=reviews,
        portfolio_summary=pf_summary,
        api_usage=usage.u,
        execution_state=exec_state,
        cost_summary=replay,
        research_summary=research_summary,
        strategy_eval=strat_eval,
    )

    # --- data-quality artifacts (incidents + health) --------------------- #
    usable_syms = [sym for sym in market_by_symbol if sym not in anomalous_symbols
                   and dq_by_symbol.get(sym) and dq_by_symbol[sym].verdict == "OK"]
    rejected_syms = [sym for sym in market_by_symbol
                     if dq_by_symbol.get(sym) and dq_by_symbol[sym].verdict != "OK"]
    data_health = dq.health(
        provider=usage.u.get("provider", "yfinance"),
        results=dq_results,
        usable=usable_syms,
        rejected=rejected_syms,
        last_run=now_ist_iso(),
        extra={"latest_workflow": "analyze", "checkpoint": cp_id, "mtm_incidents": len(getattr(pm, "last_mtm_incidents", []))},
    )
    _write_data_quality_artifacts(incidents, data_health)
    if incidents:
        payload["data_quality_warnings"].append(f"{len(incidents)} data-quality incident(s) this run — see Data Health.")

    # Persist runtime state BEFORE exporting so public/data reflects this run.
    usage.save()
    engine.save_state(exec_state)
    report.write_daily(payload)
    static_exporter.export_all()

    # --- email (daily after last checkpoint; trade/risk events) ---------- #
    es = EmailSender(settings)
    sent_info = {}
    if (checkpoint["is_last"] or args.eod) and es.should_send("daily_report"):
        subject = f"[Paper] Daily report {payload['date']} — regime {regime.regime}"
        sent_info["daily"] = es.send(subject, report.render_markdown(payload))
    if executed and es.should_send("trade_events"):
        lines = "\n".join(f"- {t['side']} {t['symbol']} x{t['quantity']} @ ₹{t.get('price')}" for t in executed)
        sent_info["trades"] = es.send(f"[Paper] {len(executed)} paper trade(s) at {cp_id}", lines)
    if reviews and es.should_send("risk_events"):
        lines = "\n".join(f"- {r['symbol']}: {r['unrealized_pnl_pct']}% → {r['label']}" for r in reviews)
        sent_info["risk"] = es.send(f"[Paper] {len(reviews)} position(s) under review", lines)
    if sent_info:
        storage.append_audit({"event": "EMAIL", "details": sent_info})

    # --- monthly report (optional) --------------------------------------- #
    if args.monthly:
        monthly = report.build_monthly(
            portfolio_summary=pf_summary,
            cost_summary=replay,
            strategy_eval=strat_eval,
            benchmark_return_pct=None,  # cumulative benchmark return not tracked in v1
            research_summary=research_summary,
            execution_state=exec_state,
        )
        report.write_monthly(monthly)
        if es.should_send("daily_report"):
            es.send(f"[Paper] Monthly report {monthly['month']}", report.render_monthly_markdown(monthly))

    print(f"[done] signals={len(signals)} executed={len(executed)} reviews={len(reviews)} "
          f"calls_today={usage.calls_today()} provider={usage.u['provider']}")
    return 0


def _audit_signal(sig, regime, adapter, engine) -> None:
    storage.append_audit({
        "event": "SIGNAL_EVALUATED",
        "symbol": sig.symbol,
        "market_regime": sig.market_regime,
        "final_recommendation": sig.label.value,
        "final_score": sig.score,
        "strategy_contributions": sig.score_breakdown,
        "risk_level": sig.risk_level.value,
        "data_quality_status": sig.data_quality.value,
        "decision_taken": "PAPER_BUY" if sig.led_to_paper_trade else sig.label.value,
        "reason": sig.reason,
        "paper_order_created": sig.led_to_paper_trade,
        "broker_adapter": adapter.name,
        "execution_mode": engine.exec_cfg.get("mode", "paper"),
        "estimated_costs": sig.estimated_cost,
        "warnings": sig.warnings,
        "conflicts": sig.conflict_warnings,
    })


def _write_data_quality_artifacts(incidents, data_health) -> None:
    """Persist data-quality incidents + health to reports and public/data.

    Incidents are appended to a rolling log (capped) so the dashboard can show
    history; data_health is the latest snapshot.
    """
    from utils import write_json  # local import to keep top clean

    log = storage.read_json(storage.report_file("data_quality_incidents.json"), [])
    if not isinstance(log, list):
        log = []
    log.extend(incidents)
    log = log[-500:]
    write_json(storage.report_file("data_quality_incidents.json"), log)
    write_json(storage.public_file("data_quality_incidents.json"), log[-100:][::-1])
    write_json(storage.report_file("data_health.json"), data_health)
    write_json(storage.public_file("data_health.json"), data_health)


def _persist_signal_history(signals) -> None:
    history = storage.load_state("signal_history", [])
    if not isinstance(history, list):
        history = []
    history.extend(s.to_dict() for s in signals)
    storage.save_state("signal_history", history[-2000:])  # cap for the browser/export


def main() -> int:
    parser = argparse.ArgumentParser(description="Indian equity paper-trading analyzer (v1: paper only).")
    parser.add_argument("--checkpoint", default="auto", help="auto | open | mid | close | manual | eod")
    parser.add_argument("--manual", action="store_true", help="manual one-off run (ignores weekday check)")
    parser.add_argument("--eod", action="store_true", help="treat as end-of-day (send daily email)")
    parser.add_argument("--monthly", action="store_true", help="also generate the end-of-month report")
    parser.add_argument("--force", action="store_true", help="run even on a non-trading day")
    args = parser.parse_args()
    try:
        return run(args)
    except Exception as exc:  # last-resort: log, email, fail safe
        storage.append_audit({"event": "SYSTEM_ERROR", "message": str(exc)})
        print(f"[ERROR] {exc}", file=sys.stderr)
        try:
            EmailSender(storage.load_config("settings.yml")).send("[Paper] System error", str(exc))
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
