#!/usr/bin/env python3
"""Finance MMG command line control surface.

Run from the repo root:
    py -3 mmg.py status
    py -3 mmg.py profile apply max-paper
    py -3 mmg.py analyze --checkpoint close --force
    py -3 mmg.py execute --checkpoint close --force
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
CONFIG = ROOT / "config"
STATE = ROOT / "data" / "state"


PROFILES: dict[str, dict[str, Any]] = {
    "conservative": {
        "description": "Original cautious paper profile: small budget, high buy threshold, 10-symbol scan.",
        "settings": {
            "capital": {
                "monthly_fake_capital": 10000,
                "max_amount_per_trade": 2000,
                "max_buys_per_day": 20,
                "max_buys_per_month": 100,
            },
            "market_data": {"max_symbols_per_run": 10},
            "rate_limits": {"sleep_seconds_between_symbols": 1},
        },
        "risk": {
            "risk": {
                "max_trade_amount": 2000,
                "monthly_capital_cap": 10000,
                "max_buys_per_day": 20,
                "max_buys_per_month": 100,
                "max_position_allocation_pct": 25,
                "allow_real_orders": False,
            }
        },
        "scoring": {
            "scoring": {
                "decision_bands": {"buy_small_paper": 80, "watch": 65},
                "buy_candidate_min_score": 80,
            },
            "hybrid_scoring": {
                "buy_threshold": 80,
                "watch_threshold": 65,
                "weights": {
                    "trend_following": 20,
                    "relative_strength": 20,
                    "market_regime": 20,
                    "volatility_risk": 15,
                    "news_event_risk": 15,
                    "portfolio_fit": 10,
                    "mean_reversion": 0,
                    "breakout": 0,
                },
                "experimental_strategies": {
                    "mean_reversion": {"enabled": True, "contributes_to_score": False, "display_only": True},
                    "breakout": {"enabled": True, "contributes_to_score": False, "display_only": True},
                },
            },
        },
    },
    "balanced": {
        "description": "More capable paper profile: moderate threshold, larger budget, full active scan.",
        "settings": {
            "capital": {
                "monthly_fake_capital": 50000,
                "max_amount_per_trade": 5000,
                "max_buys_per_day": 30,
                "max_buys_per_month": 150,
            },
            "market_data": {"max_symbols_per_run": 24},
            "rate_limits": {"sleep_seconds_between_symbols": 0.5},
        },
        "risk": {
            "risk": {
                "max_trade_amount": 5000,
                "monthly_capital_cap": 50000,
                "max_buys_per_day": 30,
                "max_buys_per_month": 150,
                "max_position_allocation_pct": 25,
                "allow_real_orders": False,
            }
        },
        "scoring": {
            "scoring": {
                "decision_bands": {"buy_small_paper": 74, "watch": 62},
                "buy_candidate_min_score": 74,
            },
            "hybrid_scoring": {
                "buy_threshold": 74,
                "watch_threshold": 62,
                "weights": {
                    "trend_following": 19,
                    "relative_strength": 20,
                    "market_regime": 18,
                    "volatility_risk": 14,
                    "news_event_risk": 15,
                    "portfolio_fit": 9,
                    "mean_reversion": 2,
                    "breakout": 3,
                },
                "experimental_strategies": {
                    "mean_reversion": {"enabled": True, "contributes_to_score": True, "display_only": False},
                    "breakout": {"enabled": True, "contributes_to_score": True, "display_only": False},
                },
            },
        },
    },
    "max-paper": {
        "description": "Maximum paper-research profile: lower buy threshold, broad scan, larger fake capital.",
        "settings": {
            "capital": {
                "monthly_fake_capital": 100000,
                "max_amount_per_trade": 10000,
                "max_buys_per_day": 50,
                "max_buys_per_month": 250,
            },
            "market_data": {"max_symbols_per_run": 34},
            "rate_limits": {"sleep_seconds_between_symbols": 0.25},
        },
        "risk": {
            "risk": {
                "max_trade_amount": 10000,
                "monthly_capital_cap": 100000,
                "max_buys_per_day": 50,
                "max_buys_per_month": 250,
                "max_position_allocation_pct": 25,
                "allow_real_orders": False,
            }
        },
        "scoring": {
            "scoring": {
                "decision_bands": {"buy_small_paper": 70, "watch": 60},
                "buy_candidate_min_score": 70,
            },
            "hybrid_scoring": {
                "buy_threshold": 70,
                "watch_threshold": 60,
                "weights": {
                    "trend_following": 18,
                    "relative_strength": 20,
                    "market_regime": 16,
                    "volatility_risk": 12,
                    "news_event_risk": 14,
                    "portfolio_fit": 8,
                    "mean_reversion": 4,
                    "breakout": 8,
                },
                "experimental_strategies": {
                    "mean_reversion": {"enabled": True, "contributes_to_score": True, "display_only": False},
                    "breakout": {"enabled": True, "contributes_to_score": True, "display_only": False},
                },
            },
        },
    },
}


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out


def parse_value(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def set_path(data: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur = data
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
        if not isinstance(cur, dict):
            raise ValueError(f"{dotted!r} crosses a non-object value at {part!r}")
    cur[parts[-1]] = value


def get_path(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    return cur


def config_file(name: str) -> Path:
    path = CONFIG / f"{name}.yml"
    if not path.exists():
        raise SystemExit(f"Unknown config file: {name}")
    return path


def run_engine(args: argparse.Namespace, no_action: bool) -> int:
    cmd = [sys.executable, str(SRC / "main.py")]
    if args.checkpoint:
        cmd += ["--checkpoint", args.checkpoint]
    if args.force:
        cmd.append("--force")
    if args.manual:
        cmd.append("--manual")
    if args.eod:
        cmd.append("--eod")
    if args.monthly:
        cmd.append("--monthly")
    if args.observe:
        cmd.append("--observe")
    if args.observe_only:
        cmd.append("--observe-only")
    if args.focused_symbol:
        cmd += ["--focused-symbol", args.focused_symbol]
    if no_action:
        cmd.append("--no-action")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    print("$ " + " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT, env=env, timeout=args.timeout)
    return completed.returncode


def cmd_analyze(args: argparse.Namespace) -> int:
    return run_engine(args, no_action=True)


def cmd_execute(args: argparse.Namespace) -> int:
    return run_engine(args, no_action=False)


def cmd_status(_: argparse.Namespace) -> int:
    settings = read_yaml(CONFIG / "settings.yml")
    risk = read_yaml(CONFIG / "risk.yml")
    scoring = read_yaml(CONFIG / "scoring.yml")
    universe = read_yaml(CONFIG / "universe.yml")
    portfolio = read_json(STATE / "portfolio.json", {})
    budget = read_json(STATE / "monthly_budget.json", {})
    execution = read_json(STATE / "execution_state.json", {})
    trades = read_json(STATE / "trade_history.json", [])
    signals = read_json(STATE / "signal_history.json", [])

    labels: dict[str, int] = {}
    for sig in signals if isinstance(signals, list) else []:
        labels[str(sig.get("label", "UNKNOWN"))] = labels.get(str(sig.get("label", "UNKNOWN")), 0) + 1

    print("Mode")
    print(f"  broker={execution.get('broker_adapter', 'unknown')} live={execution.get('live_trading_enabled')} "
          f"real_orders={execution.get('allow_real_orders')} kill_switch={execution.get('kill_switch')}")
    print("Capability")
    print(f"  profile_like={detect_profile(settings, risk, scoring)}")
    print(f"  monthly_capital={settings.get('capital', {}).get('monthly_fake_capital')} "
          f"max_trade={settings.get('capital', {}).get('max_amount_per_trade')} "
          f"risk_cap={risk.get('risk', {}).get('monthly_capital_cap')}")
    print(f"  buy_threshold={scoring.get('hybrid_scoring', {}).get('buy_threshold')} "
          f"watch_threshold={scoring.get('hybrid_scoring', {}).get('watch_threshold')} "
          f"scan={settings.get('market_data', {}).get('max_symbols_per_run')}/"
          f"{len(universe.get('active_symbols', []))}")
    print("Portfolio")
    print(f"  cash={portfolio.get('cash')} holdings={portfolio.get('holdings_value')} "
          f"total={portfolio.get('total_value')} unrealized={portfolio.get('unrealized_pnl')} "
          f"positions={len(portfolio.get('positions', []))}")
    print("Budget")
    print(f"  month={budget.get('month')} deployed={budget.get('capital_deployed')} "
          f"remaining={budget.get('capital_remaining')} buys={budget.get('buys_this_month')}/"
          f"{budget.get('max_buys_per_month')}")
    print("History")
    print(f"  trades={len(trades) if isinstance(trades, list) else 0} "
          f"signals={len(signals) if isinstance(signals, list) else 0} labels={labels}")
    return 0


def detect_profile(settings: dict[str, Any], risk: dict[str, Any], scoring: dict[str, Any]) -> str:
    for name, profile in PROFILES.items():
        expected = profile
        if (
            settings.get("capital", {}).get("monthly_fake_capital")
            == expected["settings"]["capital"]["monthly_fake_capital"]
            and risk.get("risk", {}).get("max_trade_amount") == expected["risk"]["risk"]["max_trade_amount"]
            and scoring.get("hybrid_scoring", {}).get("buy_threshold")
            == expected["scoring"]["hybrid_scoring"]["buy_threshold"]
        ):
            return name
    return "custom"


def cmd_profile(args: argparse.Namespace) -> int:
    if args.profile_command == "list":
        for name, profile in PROFILES.items():
            print(f"{name}: {profile['description']}")
        return 0
    if args.profile_command == "show":
        print(yaml.safe_dump(PROFILES[args.name], sort_keys=False))
        return 0
    if args.profile_command == "apply":
        profile = PROFILES[args.name]
        for cfg_name in ("settings", "risk", "scoring"):
            path = CONFIG / f"{cfg_name}.yml"
            current = read_yaml(path)
            updated = deep_merge(current, profile[cfg_name])
            if args.dry_run:
                print(f"--- {path.relative_to(ROOT)}")
                print(yaml.safe_dump(updated, sort_keys=False))
            else:
                write_yaml(path, updated)
        print(("Would apply" if args.dry_run else "Applied") + f" profile: {args.name}")
        return 0
    raise SystemExit("Unknown profile command")


def cmd_config(args: argparse.Namespace) -> int:
    path = config_file(args.file)
    data = read_yaml(path)
    if args.config_command == "show":
        print(yaml.safe_dump(data, sort_keys=False))
        return 0
    if args.config_command == "get":
        print(json.dumps(get_path(data, args.path), indent=2))
        return 0
    if args.config_command == "set":
        value = parse_value(args.value)
        set_path(data, args.path, value)
        write_yaml(path, data)
        print(f"Set {args.file}.{args.path} = {value!r}")
        return 0
    raise SystemExit("Unknown config command")


def cmd_history(args: argparse.Namespace) -> int:
    if args.kind == "trades":
        records = read_json(STATE / "trade_history.json", [])
    elif args.kind == "signals":
        records = read_json(STATE / "signal_history.json", [])
        if args.label:
            records = [r for r in records if r.get("label") == args.label]
    else:
        records = read_json(STATE / "audit_log.jsonl", [])
    if not isinstance(records, list):
        records = []
    for row in records[-args.limit:]:
        if args.json:
            print(json.dumps(row, ensure_ascii=False))
        elif args.kind == "signals":
            print(f"{row.get('created_at')} {row.get('symbol'):14} {row.get('label'):16} "
                  f"score={row.get('score')} traded={row.get('led_to_paper_trade')} {row.get('reason')}")
        else:
            print(json.dumps(row, ensure_ascii=False))
    return 0


def cmd_safety(_: argparse.Namespace) -> int:
    sys.path.insert(0, str(SRC))
    import storage  # type: ignore
    from broker import build_adapter  # type: ignore
    from execution_engine import ExecutionEngine  # type: ignore
    from portfolio_manager import PortfolioManager  # type: ignore
    from risk_engine import RiskEngine  # type: ignore

    configs = storage.load_all_configs()
    capital = configs["settings"].get("capital", {})
    adapter = build_adapter(
        configs["broker"].get("broker", {}).get("active_adapter", "paper"),
        starting_capital=float(capital.get("monthly_fake_capital", 10000)),
        max_trade_amount=float(capital.get("max_amount_per_trade", 2000)),
    )
    engine = ExecutionEngine(configs, adapter, RiskEngine(configs["risk"]), PortfolioManager(configs["settings"]))
    for note in engine.validate_safety():
        print(note)
    return 0


def add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint", default="auto", choices=["auto", "open", "mid", "close", "manual", "eod"])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--manual", action="store_true")
    parser.add_argument("--eod", action="store_true")
    parser.add_argument("--monthly", action="store_true")
    parser.add_argument("--observe", action="store_true")
    parser.add_argument("--observe-only", action="store_true")
    parser.add_argument("--focused-symbol")
    parser.add_argument("--timeout", type=int, default=900)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Finance MMG local CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status", help="Show engine, portfolio, budget, and history status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("safety", help="Run the execution safety gate")
    p.set_defaults(func=cmd_safety)

    p = sub.add_parser("analyze", help="Run the engine without creating paper orders")
    add_run_args(p)
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("execute", help="Run the engine and allow paper orders")
    add_run_args(p)
    p.set_defaults(func=cmd_execute)

    p = sub.add_parser("profile", help="Manage capability profiles")
    psub = p.add_subparsers(dest="profile_command", required=True)
    p_list = psub.add_parser("list", help="List profiles")
    p_list.set_defaults(func=cmd_profile)
    p_show = psub.add_parser("show", help="Show a profile")
    p_show.add_argument("name", choices=sorted(PROFILES))
    p_show.set_defaults(func=cmd_profile)
    p_apply = psub.add_parser("apply", help="Apply a profile to config files")
    p_apply.add_argument("name", choices=sorted(PROFILES))
    p_apply.add_argument("--dry-run", action="store_true")
    p_apply.set_defaults(func=cmd_profile)

    p = sub.add_parser("config", help="Inspect or edit YAML config")
    csub = p.add_subparsers(dest="config_command", required=True)
    c_show = csub.add_parser("show", help="Show config file")
    c_show.add_argument("file")
    c_show.set_defaults(func=cmd_config)
    c_get = csub.add_parser("get", help="Get dotted config value")
    c_get.add_argument("file")
    c_get.add_argument("path")
    c_get.set_defaults(func=cmd_config)
    c_set = csub.add_parser("set", help="Set dotted config value")
    c_set.add_argument("file")
    c_set.add_argument("path")
    c_set.add_argument("value")
    c_set.set_defaults(func=cmd_config)

    p = sub.add_parser("history", help="Inspect recent trades or signals")
    p.add_argument("kind", choices=["trades", "signals"])
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--label")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_history)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except subprocess.TimeoutExpired:
        print("Command timed out. Use --timeout with a larger value or reduce max_symbols_per_run.", file=sys.stderr)
        return 124
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
