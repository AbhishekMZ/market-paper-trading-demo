"""Static exporter — publish backend JSON state into public/data/.

The GitHub Pages frontend reads ONLY these files (no backend server, no secrets).
The audit log (JSONL) is converted to a JSON array for the browser.
"""
from __future__ import annotations

import os
import shutil
from typing import Any, Dict

import storage
from utils import write_json


def export_all() -> Dict[str, Any]:
    storage.ensure_dirs()
    exported = []

    # 1) latest_report.json comes from the reports dir.
    latest_report = os.path.join(storage.REPORTS_DIR, "latest_report.json")
    if os.path.exists(latest_report):
        shutil.copyfile(latest_report, os.path.join(storage.PUBLIC_DATA_DIR, "latest_report.json"))
        exported.append("latest_report.json")

    # 2) Plain state files.
    for name in ("portfolio", "trade_history", "signal_history", "api_usage", "approvals", "execution_state"):
        data = storage.load_state(name, [] if name in ("trade_history", "signal_history", "approvals") else {})
        # Cap large histories so the browser only downloads a sensible slice.
        if name == "signal_history" and isinstance(data, list):
            data = data[-250:]
        write_json(os.path.join(storage.PUBLIC_DATA_DIR, f"{name}.json"), data)
        exported.append(f"{name}.json")

    # 3) Audit log JSONL -> JSON array (most recent first, capped for the browser).
    audit = storage.read_audit()
    write_json(os.path.join(storage.PUBLIC_DATA_DIR, "audit_log.json"), audit[-500:][::-1])
    exported.append("audit_log.json")

    # 4) strategy_evaluation.json (written by the evaluator) — copy if present.
    se = os.path.join(storage.REPORTS_DIR, "strategy_evaluation.json")
    if os.path.exists(se):
        shutil.copyfile(se, os.path.join(storage.PUBLIC_DATA_DIR, "strategy_evaluation.json"))
        exported.append("strategy_evaluation.json")

    return {"exported": exported, "dir": storage.PUBLIC_DATA_DIR}
