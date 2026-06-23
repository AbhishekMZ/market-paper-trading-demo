"""DataQualityEngine — composes price-sanity + anomaly checks into one verdict.

The strategy/execution layers consult this BEFORE acting on a symbol, so a bad
or inconsistent quote can never produce a misleading paper trade or P&L.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import storage
from data_quality.anomaly_detector import detect_anomalies
from data_quality.price_sanity import check_price_consistency
from data_quality.provider_health import build_data_health
from utils import now_ist_iso, today_ist_str

# Verdicts.
OK = "OK"
DATA_ANOMALY = "DATA_ANOMALY"
STALE = "STALE"
DATA_INSUFFICIENT = "DATA_INSUFFICIENT"

_SOURCE_LOG = "dq_source_log"  # tracked under data/state via a plain json file


@dataclass
class DataQualityResult:
    symbol: str
    verdict: str
    allow_buy: bool
    price_source: Optional[str]
    entry_price_used: Optional[float]
    mtm_price_used: Optional[float]
    price_consistency_check: str
    checks: Dict[str, Any] = field(default_factory=dict)
    anomaly_flags: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    news_available: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DataQualityEngine:
    def __init__(self, data_quality_cfg: Dict[str, Any]) -> None:
        self.cfg = data_quality_cfg or {}
        self.block_on_anomaly = bool(self.cfg.get("block_buys_on_anomaly", True))
        self._source_log = self._load_source_log()

    # ------------------------------------------------------------------ #
    def assess(self, symbol: str, market_data: Dict[str, Any]) -> DataQualityResult:
        prior_source = self._source_log.get(today_ist_str(), {}).get(symbol)
        sanity = check_price_consistency(market_data, self.cfg)
        anomalies = detect_anomalies(market_data, self.cfg, prior_source)

        # Record today's source for this symbol (for next-run source-flip checks).
        current_source = sanity.get("price_source")
        if current_source:
            self._source_log.setdefault(today_ist_str(), {})[symbol] = current_source

        reasons = list(sanity["reasons"]) + list(anomalies["anomaly_reasons"])
        flags = list(anomalies["anomaly_flags"])

        # Determine verdict.
        if market_data.get("price") is None:
            verdict, allow_buy = DATA_INSUFFICIENT, False
        elif sanity["price_consistency_check"] == "FAILED" or flags:
            verdict, allow_buy = DATA_ANOMALY, False
        elif any("stale" in r for r in reasons):
            verdict, allow_buy = STALE, False
        else:
            verdict, allow_buy = OK, True

        if not self.block_on_anomaly and verdict == DATA_ANOMALY:
            allow_buy = True  # config override (not recommended)

        return DataQualityResult(
            symbol=symbol,
            verdict=verdict,
            allow_buy=allow_buy,
            price_source=sanity["price_source"],
            entry_price_used=sanity["entry_price_used"],
            mtm_price_used=sanity["mtm_price_used"],
            price_consistency_check=sanity["price_consistency_check"],
            checks={**sanity["checks"], **{"anomaly": anomalies}},
            anomaly_flags=flags,
            reasons=reasons,
            news_available=bool(market_data.get("news_available")),
        )

    def incident(self, result: DataQualityResult) -> Optional[Dict[str, Any]]:
        if result.verdict in (OK,):
            return None
        return {
            "ts": now_ist_iso(),
            "symbol": result.symbol,
            "issue": result.verdict.lower() if result.verdict != DATA_ANOMALY else "data_anomaly",
            "price_source": result.price_source,
            "entry_price": result.entry_price_used,
            "mtm_price": result.mtm_price_used,
            "price_consistency_check": result.price_consistency_check,
            "anomaly_flags": result.anomaly_flags,
            "reasons": result.reasons,
            "action": "blocked_buy_and_excluded_from_marking" if result.verdict == DATA_ANOMALY else "shown_not_traded",
        }

    def health(self, provider, results, usable, rejected, last_run=None, extra=None):
        return build_data_health(provider, [r.to_dict() for r in results], usable, rejected, last_run, extra)

    def save_source_log(self) -> None:
        # Keep only the last few days.
        days = sorted(self._source_log.keys())[-5:]
        self._source_log = {d: self._source_log[d] for d in days}
        storage.write_json(storage.state_file("dq_source_log.json"), self._source_log)

    def _load_source_log(self) -> Dict[str, Any]:
        return storage.read_json(storage.state_file("dq_source_log.json"), {})
