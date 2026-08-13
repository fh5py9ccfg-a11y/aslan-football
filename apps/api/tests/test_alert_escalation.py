from apps.api.app.alert_policy import (
    AlertIncidentService,
    AlertPolicy,
    RedisAlertPolicyRepository,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


def build():
    repo = RedisAlertPolicyRepository(
        Redis(),
        prefix="policy",
    )
    repo.save_policy(
        AlertPolicy(
            policy_id="p1",
            tenant_id="t",
            trigger=None,
            minimum_severity="LOW",
            dedup_window_seconds=10,
            acknowledge_sla_seconds=30,
            escalation_target="secondary-on-call",
            enabled=True,
            created_at=1,
        )
    )
    return repo, AlertIncidentService(repository=repo)


def test_incident_acknowledge_and_resolve():
    repo, service = build()
    incident = service.open_incident(
        alert_id="a",
        tenant_id="t",
        match_id="m",
        trigger="X",
        severity="HIGH",
        now=100,
    )

    acknowledged = service.acknowledge(
        incident_id=incident.incident_id,
        owner="ops-user",
        now=110,
    )
    resolved = service.resolve(
        incident_id=incident.incident_id,
        owner="ops-user",
        now=120,
    )

    assert acknowledged.status == "ACKNOWLEDGED"
    assert acknowledged.acknowledged_at == 110
    assert resolved.status == "RESOLVED"
    assert resolved.resolved_at == 120


def test_due_incident_is_escalated():
    repo, service = build()
    service.open_incident(
        alert_id="a",
        tenant_id="t",
        match_id="m",
        trigger="X",
        severity="HIGH",
        now=100,
    )

    escalated = service.escalate_due(
        tenant_id="t",
        now=131,
    )

    assert len(escalated) == 1
    assert escalated[0].status == "ESCALATED"
    assert escalated[0].escalation_level == 1
