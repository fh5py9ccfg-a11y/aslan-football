from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable

from .routing import Alert


@dataclass
class WebhookAlertSink:
    sender: Callable[[str, bytes, dict[str, str]], int]
    endpoint: str

    def send(self, alert: Alert) -> None:
        payload = json.dumps(
            {
                "code": alert.code,
                "severity": alert.severity.value,
                "message": alert.message,
                "deduplication_key": alert.deduplication_key,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        status = self.sender(
            self.endpoint,
            payload,
            {"Content-Type": "application/json"},
        )
        if status < 200 or status >= 300:
            raise RuntimeError(f"Alarm webhook başarısız: {status}")


@dataclass
class EmailAlertSink:
    sender: Callable[[str, str, str], None]
    recipient: str

    def send(self, alert: Alert) -> None:
        subject = f"[{alert.severity.value}] {alert.code}"
        self.sender(self.recipient, subject, alert.message)
