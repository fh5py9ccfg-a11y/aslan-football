from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class IncidentSeverity(str, Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"


@dataclass(frozen=True)
class Incident:
    incident_id: str
    title: str
    severity: IncidentSeverity
    started_at: str
    status: str
    owner: str | None


class IncidentManager:
    VALID_STATUSES = {"OPEN", "MITIGATED", "RESOLVED"}

    def create(
        self,
        *,
        incident_id: str,
        title: str,
        severity: IncidentSeverity,
        owner: str | None = None,
    ) -> Incident:
        if not incident_id.strip() or not title.strip():
            raise ValueError("Incident kimliği ve başlığı boş olamaz")
        return Incident(
            incident_id=incident_id,
            title=title,
            severity=severity,
            started_at=datetime.now(timezone.utc).isoformat(),
            status="OPEN",
            owner=owner,
        )

    def transition(self, incident: Incident, status: str) -> Incident:
        if status not in self.VALID_STATUSES:
            raise ValueError("Geçersiz incident durumu")

        allowed = {
            "OPEN": {"MITIGATED", "RESOLVED"},
            "MITIGATED": {"RESOLVED"},
            "RESOLVED": set(),
        }
        if status not in allowed[incident.status]:
            raise ValueError("Geçersiz incident geçişi")

        return Incident(
            incident_id=incident.incident_id,
            title=incident.title,
            severity=incident.severity,
            started_at=incident.started_at,
            status=status,
            owner=incident.owner,
        )
