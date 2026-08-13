from apps.api.app.alert_policy import AlertIncident
from apps.api.app.postmortem_knowledge import (
    PostmortemKnowledgeService,
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
    def get_incident(self, incident_id):
        return AlertIncident(
            incident_id=incident_id,
            alert_id="a",
            tenant_id="t",
            match_id="m",
            trigger="X",
            severity="HIGH",
            status="RESOLVED",
            owner="ops",
            created_at=1,
            acknowledged_at=2,
            resolved_at=3,
            escalation_level=0,
            escalation_target="primary",
        )


def test_completed_action_and_similarity_search():
    repository = RedisPostmortemRepository(
        Redis(),
        prefix="pm",
    )
    service = PostmortemKnowledgeService(
        repository=repository,
        incident_repository=Incidents(),
    )

    item = service.create_from_incident(
        incident_id="i1",
        title="Redis bağlantı havuzu arızası",
        summary="Canlı tahmin akışı yavaşladı",
        now=10,
    )
    item = service.update_analysis(
        postmortem_id=item.postmortem_id,
        root_cause="Redis bağlantı havuzu tükendi",
        impact="Inference gecikmesi yükseldi",
        lessons="Havuz kapasitesi izlenmeli",
        contributing_factors=("ani trafik",),
        expected_revision=item.revision,
        now=11,
    )
    item = service.add_evidence(
        postmortem_id=item.postmortem_id,
        kind="METRIC",
        summary="Pool saturation",
        reference=None,
        expected_revision=item.revision,
        now=12,
    )
    item = service.add_action(
        postmortem_id=item.postmortem_id,
        title="Pool limitini artır",
        owner="platform",
        due_at=None,
        expected_revision=item.revision,
        now=13,
    )

    action_id = item.actions[0].action_id
    item = service.complete_action(
        postmortem_id=item.postmortem_id,
        action_id=action_id,
        expected_revision=item.revision,
        now=14,
    )
    published = service.publish(
        postmortem_id=item.postmortem_id,
        expected_revision=item.revision,
        now=15,
    )

    matches = repository.search_similar(
        tenant_id="t",
        query="redis havuzu inference gecikmesi",
    )

    assert published.actions[0].status == "COMPLETED"
    assert len(matches) == 1
    assert matches[0][1] > 0
