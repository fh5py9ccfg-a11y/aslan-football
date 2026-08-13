from apps.api.app.pilot_observability import (
    PilotObservabilityService,
    RedisPilotObservabilityRepository,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


class IntelligenceRepository:
    def list_predictions(self, club_id):
        return ()

    def list_pipeline_runs(self, club_id):
        return ()

    def list_alerts(self, club_id):
        return ()


class Intelligence:
    repository = IntelligenceRepository()


def build():
    redis = Redis()
    return PilotObservabilityService(
        repository=RedisPilotObservabilityRepository(
            redis,
            prefix="obs",
        ),
        intelligence_service=Intelligence(),
    )


def test_health_score_and_alarm_generation():
    service = build()
    service.record_event(
        event_id="e1",
        club_id="c1",
        category="API",
        severity="ERROR",
        component="api",
        message="Timeout",
        duration_ms=700,
        now=100,
    )
    service.open_incident(
        incident_id="i1",
        club_id="c1",
        title="API timeout",
        severity="ERROR",
        component="api",
        owner="ops",
        description="Pilot hata",
        now=101,
    )

    report = service.health_score(
        report_id="h1",
        club_id="c1",
        now=102,
    )
    alarms = service.generate_alarm_events(
        club_id="c1",
        now=103,
    )

    assert report.health_score < 100
    assert report.status in {
        "HEALTHY",
        "DEGRADED",
        "UNHEALTHY",
    }
    assert len(alarms) >= 1


def test_incident_can_be_resolved():
    service = build()
    service.open_incident(
        incident_id="i1",
        club_id="c1",
        title="Issue",
        severity="WARNING",
        component="worker",
        owner="ops",
        description="",
        now=100,
    )
    resolved = service.update_incident(
        incident_id="i1",
        status="RESOLVED",
        now=110,
    )

    assert resolved.status == "RESOLVED"
    assert resolved.resolved_at == 110
