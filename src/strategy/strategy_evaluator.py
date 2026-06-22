"""StrategyEvaluator — measure how each strategy actually performed.

Reads signal_history + trade_history + portfolio (closed positions) and
attributes outcomes back to the strategies that contributed to each buy. It is
deterministic and only uses data already recorded (no look-ahead).

Outputs:
  data/reports/strategy_evaluation.json
  data/reports/strategy_evaluation.md
  public/data/strategy_evaluation.json

NOTE on honesty: with only ~1 month of paper data these metrics are indicative,
not conclusive. The markdown report says so explicitly.
"""
from __future__ import annotations

import os
import statistics
from typing import Any, Dict, List

import storage
from utils import now_ist_iso, write_json


def _new_metrics() -> Dict[str, Any]:
    return {
        "signals_generated": 0,
        "paper_trades_triggered": 0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.0,
        "gains": [],          # temp; removed before output
        "losses_list": [],    # temp; removed before output
        "average_gain": 0.0,
        "average_loss": 0.0,
        "false_positive_count": 0,
        "avoided_bad_trade_count": 0,
        "score_contributions": [],  # temp
        "average_score_contribution": 0.0,
        "confidence_accuracy": None,
        "notes": "",
    }


class StrategyEvaluator:
    def __init__(self) -> None:
        self.signals = storage.load_state("signal_history", [])
        self.trades = storage.load_state("trade_history", [])
        self.portfolio = storage.load_state("portfolio", {})
        if not isinstance(self.signals, list):
            self.signals = []
        if not isinstance(self.trades, list):
            self.trades = []
        self._signal_by_id = {s.get("signal_id"): s for s in self.signals}

    # ------------------------------------------------------------------ #
    def evaluate(self) -> Dict[str, Any]:
        metrics: Dict[str, Dict[str, Any]] = {}

        # 1) signals_generated + score contributions + avoided-bad-trade.
        avoid_labels = {"DO_NOT_BUY", "HIGH_RISK_IGNORE", "NO_ACTION"}
        for sig in self.signals:
            label = sig.get("label")
            for res in sig.get("strategy_results", []):
                if not res.get("contributes_to_score"):
                    continue
                name = res.get("strategy_name")
                m = metrics.setdefault(name, _new_metrics())
                m["signals_generated"] += 1
                m["score_contributions"].append(res.get("score_contribution", 0))
                if res.get("signal") == "NEGATIVE" and label in avoid_labels:
                    m["avoided_bad_trade_count"] += 1

        # 2) Attribute closed-position outcomes to opening-buy strategies.
        closed = self.portfolio.get("closed_positions", [])
        buy_trades = [t for t in self.trades if t.get("side") == "BUY" and t.get("status") == "FILLED"]
        for cp in closed:
            symbol = cp.get("symbol")
            realized = float(cp.get("realized_pnl", 0.0))
            # Find the opening buy for this symbol (latest before close).
            opening = next((t for t in reversed(buy_trades) if t.get("symbol") == symbol), None)
            sig = self._signal_by_id.get(opening.get("signal_id")) if opening else None
            contributors = (
                [r.get("strategy_name") for r in sig.get("strategy_results", []) if r.get("contributes_to_score")]
                if sig else []
            )
            for name in contributors:
                m = metrics.setdefault(name, _new_metrics())
                if realized >= 0:
                    m["wins"] += 1
                    m["gains"].append(realized)
                else:
                    m["losses"] += 1
                    m["losses_list"].append(realized)
                    m["false_positive_count"] += 1

        # 3) paper_trades_triggered: buys whose signal counted each strategy.
        for t in buy_trades:
            sig = self._signal_by_id.get(t.get("signal_id"))
            if not sig:
                continue
            for r in sig.get("strategy_results", []):
                if r.get("contributes_to_score"):
                    metrics.setdefault(r.get("strategy_name"), _new_metrics())["paper_trades_triggered"] += 1

        # 4) Finalize derived metrics.
        for name, m in metrics.items():
            total = m["wins"] + m["losses"]
            m["win_rate"] = round(m["wins"] / total * 100, 1) if total else 0.0
            m["average_gain"] = round(statistics.fmean(m["gains"]), 2) if m["gains"] else 0.0
            m["average_loss"] = round(statistics.fmean(m["losses_list"]), 2) if m["losses_list"] else 0.0
            m["average_score_contribution"] = (
                round(statistics.fmean(m["score_contributions"]), 1) if m["score_contributions"] else 0.0
            )
            m["notes"] = self._note(m)
            del m["gains"], m["losses_list"], m["score_contributions"]

        result = {
            "as_of": now_ist_iso(),
            "portfolio_max_drawdown_pct": float(self.portfolio.get("max_drawdown_pct", 0.0)),
            "total_signals": len(self.signals),
            "total_paper_trades": len([t for t in self.trades if t.get("status") == "FILLED"]),
            "strategies": metrics,
            "disclaimer": (
                "Indicative only. One month of paper data is not enough to conclude a strategy works. "
                "No weights were changed automatically during the month."
            ),
        }
        self._write(result)
        return result

    @staticmethod
    def _note(m: Dict[str, Any]) -> str:
        if m["paper_trades_triggered"] == 0:
            return "No paper trades yet attributed; acting mainly as a filter."
        if m["win_rate"] >= 55 and m["wins"] + m["losses"] >= 3:
            return "Positive so far, but sample is small — keep paper testing."
        if m["losses"] > m["wins"]:
            return "Net negative attribution so far — review before increasing weight."
        return "Insufficient sample to judge; continue paper testing."

    def _write(self, result: Dict[str, Any]) -> None:
        storage.ensure_dirs()
        write_json(os.path.join(storage.REPORTS_DIR, "strategy_evaluation.json"), result)
        write_json(os.path.join(storage.PUBLIC_DATA_DIR, "strategy_evaluation.json"), result)
        with open(os.path.join(storage.REPORTS_DIR, "strategy_evaluation.md"), "w", encoding="utf-8") as fh:
            fh.write(self._markdown(result))

    @staticmethod
    def _markdown(result: Dict[str, Any]) -> str:
        lines = [
            "# Strategy Evaluation",
            "",
            f"_As of {result['as_of']}_",
            "",
            f"- Total signals: **{result['total_signals']}**",
            f"- Total paper trades: **{result['total_paper_trades']}**",
            f"- Portfolio max drawdown: **{result['portfolio_max_drawdown_pct']:.2f}%**",
            "",
            "> " + result["disclaimer"],
            "",
            "| Strategy | Signals | Trades | Wins | Losses | Win% | Avg Gain | Avg Loss | Avoided Bad | Avg Score | Notes |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for name, m in sorted(result["strategies"].items()):
            lines.append(
                f"| {name} | {m['signals_generated']} | {m['paper_trades_triggered']} | {m['wins']} | "
                f"{m['losses']} | {m['win_rate']} | {m['average_gain']} | {m['average_loss']} | "
                f"{m['avoided_bad_trade_count']} | {m['average_score_contribution']} | {m['notes']} |"
            )
        lines.append("")
        return "\n".join(lines)
