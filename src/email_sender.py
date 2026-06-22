"""Email sender (Gmail SMTP, app password).

Email is the ONLY notification channel in v1 (WhatsApp/Telegram disabled).
Credentials come from the environment and are NEVER logged or committed:
    GMAIL_USER, GMAIL_APP_PASSWORD, ALERT_EMAIL_TO

If credentials are missing or email is disabled, sending is skipped gracefully
(the run still succeeds — email is best-effort).
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, Optional

from utils import env_bool


class EmailSender:
    def __init__(self, settings: Dict[str, Any]) -> None:
        notif = settings.get("notifications", {})
        self.enabled = bool(notif.get("email_enabled", True)) and env_bool("EMAIL_ENABLED", True)
        self.send_on = notif.get("send_on", {})
        self.default_to = os.environ.get("ALERT_EMAIL_TO") or notif.get("alert_email_to", "sahabhi115@gmail.com")
        self.user = os.environ.get("GMAIL_USER", "").strip()
        self.password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
        self.host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.environ.get("SMTP_PORT", "465"))

    def _can_send(self) -> bool:
        return bool(self.enabled and self.user and self.password and self.default_to)

    def should_send(self, event: str) -> bool:
        return bool(self.send_on.get(event, True))

    def send(self, subject: str, body_markdown: str, to: Optional[str] = None) -> Dict[str, Any]:
        recipient = to or self.default_to
        if not self._can_send():
            return {"sent": False, "reason": "Email disabled or credentials/recipient missing.",
                    "recipient": recipient}
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.user
        msg["To"] = recipient
        msg.set_content(body_markdown)
        # Minimal HTML wrapper (keeps Markdown readable in clients).
        html = "<pre style='font-family:ui-monospace,Menlo,monospace;white-space:pre-wrap'>" + \
               _escape(body_markdown) + "</pre>"
        msg.add_alternative(html, subtype="html")
        try:
            if self.port == 465:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=30) as srv:
                    srv.login(self.user, self.password)
                    srv.send_message(msg)
            else:
                with smtplib.SMTP(self.host, self.port, timeout=30) as srv:
                    srv.starttls()
                    srv.login(self.user, self.password)
                    srv.send_message(msg)
            return {"sent": True, "recipient": recipient}
        except Exception as exc:
            return {"sent": False, "reason": f"SMTP error: {exc}", "recipient": recipient}


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
