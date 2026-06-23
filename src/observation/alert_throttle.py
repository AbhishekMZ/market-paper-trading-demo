"""AlertThrottle — per-run caps on escalations and emails.

In-memory for a single run (the cross-run dedup lives in CooldownManager). Bounds
how many escalations and how many emails one observation run may emit, and
de-duplicates identical email keys within the run.
"""
from __future__ import annotations

from typing import Any, Dict, Set


class AlertThrottle:
    def __init__(self, cfg: Dict[str, Any]) -> None:
        esc = (cfg or {}).get("escalation", {})
        self.max_escalations = int(esc.get("max_escalations_per_run", 5))
        self.max_emails = int(esc.get("max_email_alerts_per_run", 5))
        self._escalations = 0
        self._emails = 0
        self._email_keys: Set[str] = set()

    def can_escalate(self) -> bool:
        return self._escalations < self.max_escalations

    def record_escalation(self) -> None:
        self._escalations += 1

    def can_email(self, key: str) -> bool:
        return self._emails < self.max_emails and key not in self._email_keys

    def record_email(self, key: str) -> None:
        self._emails += 1
        self._email_keys.add(key)

    @property
    def emails_sent(self) -> int:
        return self._emails
