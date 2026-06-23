"""Offline, deterministic tests for the Observation & Escalation Engine.

Run:  python scripts/test_observation_engine.py

Covers the safety-critical behavior with fakes (no network, no real pipeline):
  * trigger rules fire correctly (breakout / hard-loss / critical-news / data
    anomaly / regime shift) and set blocks_action where required;
  * escalation takes a SWIFT PAPER BUY only via ExecutionEngine, and only when
    allowed — suppressed by --no-action, by news blocks, and by cooldown;
  * cooldowns + per-run throttle stop duplicate alerts.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import storage  # noqa: E402
from utils import write_json  # noqa: E402
from observation.alert_throttle import AlertThrottle  # noqa: E402
from observation.cooldown_manager import CooldownManager  # noqa: E402
from observation.escalation_engine import EscalationEngine  # noqa: E402
from observation.trigger_models import ActionType, TriggerType  # noqa: E402
from observation.trigger_rules import TriggerRules  # noqa: E402
from order_models import DataQuality, RiskLevel, SignalLabel, OrderState, TradeSignal  # noqa: E402


class FakeDQ:
    def __init__(self, verdict): self.verdict = verdict; self.anomaly_flags = []


class FakeEmail:
    def send(self, subject, body, to=None): return {"sent": False, "reason": "test"}


class FakeOrderResult:
    status = OrderState.FILLED
    quantity = 3
    price = 100.0
    amount = 300.0
    order_id = "ord-test"


class FakeEngine:
    """Stands in for ExecutionEngine; records that process_buy was called."""
    def __init__(self): self.max_trade_amount = 2000.0; self.called = 0
    def process_buy(self, signal, amount_cap, prices, checkpoint=""):
        self.called += 1
        return FakeOrderResult()


def _buy_sig():
    return TradeSignal(signal_id="t", symbol="ABC.NS", name="ABC", exchange="NSE", score=85.0,
                       label=SignalLabel.BUY_SMALL_PAPER, risk_level=RiskLevel.LOW, confidence=0.7,
                       data_quality=DataQuality.GOOD, reason="breakout")


class FakeFocused:
    def __init__(self, blocked_by=None, action_allowed=True):
        self.blocked_by = blocked_by; self.action_allowed = action_allowed
    def analyze(self, symbol, meta, context, market_data=None, prefetched_news=None):
        return {"signal": _buy_sig(), "market_data": {"price": 100.0},
                "result": {"action_allowed": self.action_allowed, "blocked_by": self.blocked_by,
                           "manual_review": False, "label": "BUY_SMALL_PAPER", "score": 85.0,
                           "news_risk_level": "NONE", "data_quality_verdict": "OK"}}


def main() -> int:
    obs_cfg = storage.load_config("observation.yml").get("observation", {})
    write_json(storage.state_file("alert_cooldowns.json"), {})  # clean slate
    rules = TriggerRules(obs_cfg)
    md = {"price": 110.0, "change_pct": 1.0, "previous_close": 109.0,
          "graph": [{"price": p} for p in [100, 101, 102, 103, 104, 105]]}

    # --- trigger rules -------------------------------------------------- #
    trs = rules.evaluate_symbol("ABC.NS", "ABC", md, {"last_price": 108.0}, None, None,
                                FakeDQ("OK"), is_buy_candidate=True, regime="RISK_ON")
    bo = next(t for t in trs if t.trigger_type == TriggerType.PRICE_BREAKOUT)
    assert bo.requires_focused_analysis, "breakout on a buy candidate must request focused analysis"

    anom = rules.evaluate_symbol("ABC.NS", "ABC", md, {}, None, None, FakeDQ("DATA_ANOMALY"), True, "RISK_ON")
    assert anom and anom[0].trigger_type == TriggerType.DATA_ANOMALY and anom[0].blocks_action

    loss = rules.evaluate_symbol("ABC.NS", "ABC", md, {}, {"unrealized_pnl_pct": -16.0}, None,
                                 FakeDQ("OK"), False, "RISK_ON")
    assert any(t.trigger_type == TriggerType.HARD_LOSS_REVIEW for t in loss)

    crit = rules.evaluate_symbol("ABC.NS", "ABC", md, {}, None, {"news_risk_level": "CRITICAL"},
                                 FakeDQ("OK"), True, "RISK_ON")
    assert any(t.trigger_type == TriggerType.CRITICAL_NEWS and t.blocks_action for t in crit)

    rt = rules.evaluate_regime("RISK_OFF", "RISK_ON")
    assert rt and rt.trigger_type == TriggerType.MARKET_REGIME_SHIFT and rt.blocks_action

    # --- escalation: SWIFT PAPER BUY only via ExecutionEngine ----------- #
    ctx = {"held_symbols": [], "meta_by_symbol": {"ABC.NS": {}},
           "market_data_by_symbol": {"ABC.NS": md}, "news_raw_by_symbol": {"ABC.NS": []}}

    def make_esc(no_action=False, focused=None):
        write_json(storage.state_file("alert_cooldowns.json"), {})
        cd = CooldownManager(obs_cfg)
        th = AlertThrottle(obs_cfg)
        eng = FakeEngine()
        e = EscalationEngine(obs_cfg, eng, focused or FakeFocused(), cd, th, FakeEmail(), no_action=no_action)
        return e, eng

    # allowed -> swift paper buy through the engine
    e, eng = make_esc()
    out = e.process([bo], ctx)
    assert eng.called == 1, "must place the paper buy through ExecutionEngine"
    assert out["escalations"][0]["action_type"] == ActionType.PAPER_BUY_ALLOWED.value
    assert len(out["actions_taken"]) == 1

    # --no-action -> review only, engine NOT called
    e, eng = make_esc(no_action=True)
    out = e.process([bo], ctx)
    assert eng.called == 0, "--no-action must not place any order"
    assert out["escalations"][0]["action_type"] == ActionType.PAPER_BUY_REVIEW.value

    # news block in focused analysis -> blocked, engine NOT called
    e, eng = make_esc(focused=FakeFocused(blocked_by="NEWS", action_allowed=False))
    out = e.process([bo], ctx)
    assert eng.called == 0 and out["escalations"][0]["action_type"] == ActionType.BLOCKED_BY_NEWS.value

    # --- cooldown + throttle ------------------------------------------- #
    write_json(storage.state_file("alert_cooldowns.json"), {})
    cd = CooldownManager(obs_cfg)
    assert not cd.trigger_on_cooldown("ABC.NS", "PRICE_BREAKOUT")
    cd.stamp_alert("ABC.NS", "PRICE_BREAKOUT")
    assert cd.trigger_on_cooldown("ABC.NS", "PRICE_BREAKOUT"), "duplicate alert must be on cooldown"

    th = AlertThrottle(obs_cfg)
    fired = 0
    while th.can_escalate():
        th.record_escalation(); fired += 1
    assert fired == th.max_escalations

    write_json(storage.state_file("alert_cooldowns.json"), {})  # leave clean
    print("OK: all observation/escalation safety invariants hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
