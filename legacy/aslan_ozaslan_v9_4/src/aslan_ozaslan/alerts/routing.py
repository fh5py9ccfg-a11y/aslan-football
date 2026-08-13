from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Alert:
    code: str
    severity: AlertSeverity
    message: str
    deduplication_key: str


class AlertSink(Protocol):
    def send(self, alert: Alert) -> None:
        ...


class InMemoryAlertSink:
    def __init__(self):
        self.alerts: list[Alert] = []

    def send(self, alert: Alert) -> None:
        self.alerts.append(alert)


class AlertRouter:
    def __init__(self, routes: dict[AlertSeverity, list[AlertSink]]):
        self.routes = {severity: list(sinks) for severity, sinks in routes.items()}
        self._seen_keys: set[str] = set()

    def route(self, alert: Alert) -> bool:
        if not alert.code.strip() or not alert.message.strip():
            raise ValueError("Alarm kodu ve mesajı boş olamaz")
        if alert.deduplication_key in self._seen_keys:
            return False
        sinks = self.routes.get(alert.severity, [])
        for sink in sinks:
            sink.send(alert)
        self._seen_keys.add(alert.deduplication_key)
        return True
