from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class TelemetryEvent:
    event_id: str
    club_id: str
    category: str
    severity: str
    component: str
    message: str
    duration_ms: int
    created_at: int


@dataclass(frozen=True)
class Incident:
    incident_id: str
    club_id: str
    title: str
    severity: str
    status: str
    component: str
    owner: str
    description: str
    opened_at: int
    resolved_at: int


@dataclass(frozen=True)
class HealthScoreReport:
    report_id: str
    club_id: str
    event_count: int
    error_count: int
    warning_count: int
    p95_duration_ms: float
    open_incidents: int
    health_score: float
    status: str
    generated_at: int


@dataclass(frozen=True)
class DailyPilotSummary:
    summary_id: str
    club_id: str
    day_key: str
    telemetry_events: int
    predictions_created: int
    pipeline_runs: int
    alerts_created: int
    incidents_opened: int
    incidents_resolved: int
    average_duration_ms: float
    generated_at: int


class ObservabilityValidationError(ValueError):
    pass


class RedisPilotObservabilityRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:pilot-observability",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_event(self, item: TelemetryEvent) -> TelemetryEvent:
        self.client.setex(
            self._event_key(item.event_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_event_index(item.club_id),
            item.event_id,
        )
        return item

    def list_events(
        self,
        club_id: str,
    ) -> tuple[TelemetryEvent, ...]:
        items = []
        for event_id in self.client.smembers(
            self._club_event_index(club_id)
        ):
            if isinstance(event_id, bytes):
                event_id = event_id.decode("utf-8")
            payload = self.client.get(
                self._event_key(str(event_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                TelemetryEvent(**json.loads(payload))
            )
        items.sort(key=lambda item: item.created_at)
        return tuple(items)

    def save_incident(self, item: Incident) -> Incident:
        self.client.setex(
            self._incident_key(item.incident_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_incident_index(item.club_id),
            item.incident_id,
        )
        return item

    def get_incident(
        self,
        incident_id: str,
    ) -> Incident | None:
        payload = self.client.get(
            self._incident_key(incident_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return Incident(**json.loads(payload))

    def list_incidents(
        self,
        club_id: str,
    ) -> tuple[Incident, ...]:
        items = []
        for incident_id in self.client.smembers(
            self._club_incident_index(club_id)
        ):
            if isinstance(incident_id, bytes):
                incident_id = incident_id.decode("utf-8")
            item = self.get_incident(str(incident_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.opened_at, reverse=True)
        return tuple(items)

    def _event_key(self, event_id: str) -> str:
        return f"{self.prefix}:event:{event_id}"

    def _club_event_index(self, club_id: str) -> str:
        return f"{self.prefix}:events:{club_id}"

    def _incident_key(self, incident_id: str) -> str:
        return f"{self.prefix}:incident:{incident_id}"

    def _club_incident_index(self, club_id: str) -> str:
        return f"{self.prefix}:incidents:{club_id}"


class PilotObservabilityService:
    CATEGORIES = {
        "API",
        "PREDICTION",
        "PIPELINE",
        "INTEGRATION",
        "SECURITY",
        "BACKUP",
    }
    SEVERITIES = {
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }
    INCIDENT_STATUSES = {
        "OPEN",
        "INVESTIGATING",
        "MITIGATED",
        "RESOLVED",
    }

    def __init__(
        self,
        *,
        repository,
        intelligence_service,
    ):
        self.repository = repository
        self.intelligence_service = intelligence_service

    def record_event(
        self,
        *,
        event_id: str,
        club_id: str,
        category: str,
        severity: str,
        component: str,
        message: str,
        duration_ms: int = 0,
        now: int | None = None,
    ) -> TelemetryEvent:
        normalized_category = category.upper()
        normalized_severity = severity.upper()
        if normalized_category not in self.CATEGORIES:
            raise ObservabilityValidationError(
                "Geçersiz telemetri kategorisi"
            )
        if normalized_severity not in self.SEVERITIES:
            raise ObservabilityValidationError(
                "Geçersiz telemetri seviyesi"
            )
        if duration_ms < 0:
            raise ObservabilityValidationError(
                "Süre negatif olamaz"
            )
        item = TelemetryEvent(
            event_id=event_id,
            club_id=club_id,
            category=normalized_category,
            severity=normalized_severity,
            component=component.strip(),
            message=message.strip(),
            duration_ms=duration_ms,
            created_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_event(item)

    def open_incident(
        self,
        *,
        incident_id: str,
        club_id: str,
        title: str,
        severity: str,
        component: str,
        owner: str,
        description: str,
        now: int | None = None,
    ) -> Incident:
        normalized = severity.upper()
        if normalized not in self.SEVERITIES:
            raise ObservabilityValidationError(
                "Geçersiz incident seviyesi"
            )
        item = Incident(
            incident_id=incident_id,
            club_id=club_id,
            title=title.strip(),
            severity=normalized,
            status="OPEN",
            component=component.strip(),
            owner=owner.strip(),
            description=description.strip(),
            opened_at=int(
                now if now is not None else time.time()
            ),
            resolved_at=0,
        )
        return self.repository.save_incident(item)

    def update_incident(
        self,
        *,
        incident_id: str,
        status: str,
        owner: str | None = None,
        now: int | None = None,
    ) -> Incident:
        current = self.repository.get_incident(incident_id)
        if current is None:
            raise KeyError("Incident bulunamadı")
        normalized = status.upper()
        if normalized not in self.INCIDENT_STATUSES:
            raise ObservabilityValidationError(
                "Geçersiz incident durumu"
            )
        updated = Incident(
            **{
                **current.__dict__,
                "status": normalized,
                "owner": (
                    owner.strip()
                    if owner is not None
                    else current.owner
                ),
                "resolved_at": (
                    int(now if now is not None else time.time())
                    if normalized == "RESOLVED"
                    else current.resolved_at
                ),
            }
        )
        return self.repository.save_incident(updated)

    def health_score(
        self,
        *,
        report_id: str,
        club_id: str,
        now: int | None = None,
    ) -> HealthScoreReport:
        events = self.repository.list_events(club_id)
        incidents = self.repository.list_incidents(club_id)
        errors = [
            item
            for item in events
            if item.severity in {"ERROR", "CRITICAL"}
        ]
        warnings = [
            item
            for item in events
            if item.severity == "WARNING"
        ]
        durations = sorted(
            item.duration_ms
            for item in events
            if item.duration_ms > 0
        )
        p95 = 0.0
        if durations:
            index = max(
                0,
                min(
                    len(durations) - 1,
                    int(len(durations) * 0.95) - 1,
                ),
            )
            p95 = float(durations[index])
        open_incidents = sum(
            1
            for item in incidents
            if item.status != "RESOLVED"
        )

        penalty = (
            len(errors) * 7
            + len(warnings) * 2
            + open_incidents * 10
            + (10 if p95 > 500 else 5 if p95 > 250 else 0)
        )
        score = max(0.0, 100.0 - penalty)
        status = (
            "HEALTHY"
            if score >= 90
            else "DEGRADED"
            if score >= 70
            else "UNHEALTHY"
        )
        return HealthScoreReport(
            report_id=report_id,
            club_id=club_id,
            event_count=len(events),
            error_count=len(errors),
            warning_count=len(warnings),
            p95_duration_ms=round(p95, 2),
            open_incidents=open_incidents,
            health_score=round(score, 2),
            status=status,
            generated_at=int(
                now if now is not None else time.time()
            ),
        )

    def generate_alarm_events(
        self,
        *,
        club_id: str,
        now: int | None = None,
    ) -> tuple[TelemetryEvent, ...]:
        report = self.health_score(
            report_id=f"auto-health:{club_id}",
            club_id=club_id,
            now=now,
        )
        generated = []
        current = int(now if now is not None else time.time())

        def add(severity: str, message: str):
            event = TelemetryEvent(
                event_id=(
                    f"alarm:{club_id}:{current}:{len(generated)+1}"
                ),
                club_id=club_id,
                category="API",
                severity=severity,
                component="observability",
                message=message,
                duration_ms=0,
                created_at=current,
            )
            self.repository.save_event(event)
            generated.append(event)

        if report.status == "UNHEALTHY":
            add(
                "CRITICAL",
                "Sistem sağlık skoru kritik seviyede",
            )
        elif report.status == "DEGRADED":
            add(
                "WARNING",
                "Sistem sağlık skoru düşüyor",
            )
        if report.p95_duration_ms > 500:
            add(
                "ERROR",
                "p95 yanıt süresi 500 ms eşiğini aştı",
            )
        if report.open_incidents >= 3:
            add(
                "CRITICAL",
                "Üç veya daha fazla açık incident var",
            )
        if not generated:
            add(
                "INFO",
                "Alarm eşiği ihlali yok",
            )
        return tuple(generated)

    def daily_summary(
        self,
        *,
        summary_id: str,
        club_id: str,
        day_key: str,
        now: int | None = None,
    ) -> DailyPilotSummary:
        events = self.repository.list_events(club_id)
        incidents = self.repository.list_incidents(club_id)
        predictions = (
            self.intelligence_service.repository
            .list_predictions(club_id)
        )
        pipeline_runs = (
            self.intelligence_service.repository
            .list_pipeline_runs(club_id)
        )
        alerts = (
            self.intelligence_service.repository
            .list_alerts(club_id)
        )
        durations = [
            item.duration_ms
            for item in events
            if item.duration_ms > 0
        ]
        average_duration = (
            sum(durations) / len(durations)
            if durations
            else 0.0
        )
        return DailyPilotSummary(
            summary_id=summary_id,
            club_id=club_id,
            day_key=day_key,
            telemetry_events=len(events),
            predictions_created=len(predictions),
            pipeline_runs=len(pipeline_runs),
            alerts_created=len(alerts),
            incidents_opened=len(incidents),
            incidents_resolved=sum(
                1
                for item in incidents
                if item.status == "RESOLVED"
            ),
            average_duration_ms=round(
                average_duration,
                2,
            ),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
