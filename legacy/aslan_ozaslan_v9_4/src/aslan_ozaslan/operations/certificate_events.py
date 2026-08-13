from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class CertificateEvent:
    certificate_name: str
    event_type: str
    occurred_at: str
    detail: str


class CertificateEventRecorder:
    VALID_TYPES = {"ISSUED", "RENEWED", "FAILED", "EXPIRING"}

    def __init__(self):
        self._events: list[CertificateEvent] = []

    def record(self, certificate_name: str, event_type: str, detail: str) -> CertificateEvent:
        if event_type not in self.VALID_TYPES:
            raise ValueError("Geçersiz sertifika olayı")
        if not certificate_name.strip():
            raise ValueError("Sertifika adı boş olamaz")

        event = CertificateEvent(
            certificate_name=certificate_name,
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            detail=detail,
        )
        self._events.append(event)
        return event

    def recent(self, limit: int = 100) -> tuple[CertificateEvent, ...]:
        if limit <= 0:
            raise ValueError("limit pozitif olmalıdır")
        return tuple(self._events[-limit:][::-1])
