import pytest

from apps.api.app.alert_policy import AlertIncident
from apps.api.app.postmortem_knowledge import (
    PostmortemConflict,
    PostmortemKnowledgeService,
    PostmortemValidationError,
    RedisPostmortemRepository,
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


class Incidents:
    def __init__(self, status="RESOLVED"):
        self.item = AlertIncident(
            incident_id="i1",
            alert_id="a1",
            tenant_id="tenant-a",
            match_id="m1",
            trigger="STREAM_ANOMALY",
            severity="HIGH",
            status=status,
            owner="ops",
            created_at=10,
            acknowledged_at=20,
            resolved_at=30 if status == "RESOLVED" else None,
            escalation_level=0,
            escalation_target="primary",
        )

    def get_incident(self, incident_id):
        return self.item if incident_id == "i1" else None


def build(status="RESOLVED"):
    repository = RedisPostmortemRepository(
        Redis(),
        prefix="pm",
    )
    service = PostmortemKnowledgeService(
        repository=repository,
        incident_repository=Incidents(status),
    )
    return repository, service


def complete_draft(service):
    item = service.create_from_incident(
        incident_id="i1",
        title="Streaming gecikmesi",
        summary="Canlı event işleme gecikti",
        now=100,
    )
    item = service.update_analysis(
        postmortem_id=item.postmortem_id,
        root_cause="Redis bağlantı havuzu tükendi",
        impact="Canlı kararlar gecikti",
        lessons="Kapasite alarmı erkene alınmalı",
        contributing_factors=(
            "yük artışı",
            "düşük havuz limiti",
        ),
        expected_revision=item.revision,
        now=101,
    )
    item = service.add_evidence(
        postmortem_id=item.postmortem_id,
        kind="METRIC",
        summary="Bağlantı kullanımı yüzde yüz oldu",
        reference="grafana://redis-pool",
        expected_revision=item.revision,
        now=102,
    )
    item = service.add_action(
        postmortem_id=item.postmortem_id,
        title="Redis pool limitini yükselt",
        owner="platform-team",
        due_at=200,
        expected_revision=item.revision,
        now=103,
    )
    return item


def test_complete_postmortem_can_be_published():
    repository, service = build()
    item = complete_draft(service)

    published = service.publish(
        postmortem_id=item.postmortem_id,
        expected_revision=item.revision,
        now=104,
    )

    assert published.status == "PUBLISHED"
    assert published.published_at == 104
    assert len(
        repository.list_tenant(
            "tenant-a",
            status="PUBLISHED",
        )
    ) == 1


def test_open_incident_cannot_be_published():
    _, service = build(status="OPEN")
    item = complete_draft(service)

    with pytest.raises(PostmortemValidationError):
        service.publish(
            postmortem_id=item.postmortem_id,
            expected_revision=item.revision,
            now=104,
        )


def test_revision_conflict_is_detected():
    _, service = build()
    item = service.create_from_incident(
        incident_id="i1",
        title="Incident",
        summary="Summary",
        now=100,
    )

    with pytest.raises(PostmortemConflict):
        service.update_analysis(
            postmortem_id=item.postmortem_id,
            root_cause="Root cause",
            impact="Impact",
            lessons="Lessons",
            contributing_factors=(),
            expected_revision=99,
            now=101,
        )


def test_published_postmortem_is_immutable():
    _, service = build()
    item = complete_draft(service)
    published = service.publish(
        postmortem_id=item.postmortem_id,
        expected_revision=item.revision,
        now=104,
    )

    with pytest.raises(PostmortemConflict):
        service.add_evidence(
            postmortem_id=published.postmortem_id,
            kind="LOG",
            summary="Late evidence",
            reference=None,
            expected_revision=published.revision,
            now=105,
        )
