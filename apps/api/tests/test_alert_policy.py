from apps.api.app.alert_policy import (
    AlertIncidentService,
    AlertPolicy,
    RedisAlertPolicyRepository,
    SilenceRule,
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
            tenant_id="tenant-a",
            trigger="MOMENTUM_SHIFT",
            minimum_severity="MEDIUM",
            dedup_window_seconds=60,
            acknowledge_sla_seconds=30,
            escalation_target="on-call-primary",
            enabled=True,
            created_at=100,
        )
    )
    return repo, AlertIncidentService(
        repository=repo
    )


def test_policy_opens_incident():
    repo, service = build()

    incident = service.open_incident(
        alert_id="a1",
        tenant_id="tenant-a",
        match_id="m1",
        trigger="MOMENTUM_SHIFT",
        severity="HIGH",
        now=100,
    )

    assert incident is not None
    assert incident.status == "OPEN"
    assert incident.escalation_target == "on-call-primary"


def test_dedup_suppresses_duplicate_incident():
    repo, service = build()

    first = service.open_incident(
        alert_id="a1",
        tenant_id="tenant-a",
        match_id="m1",
        trigger="MOMENTUM_SHIFT",
        severity="HIGH",
        now=100,
    )
    second = service.open_incident(
        alert_id="a2",
        tenant_id="tenant-a",
        match_id="m1",
        trigger="MOMENTUM_SHIFT",
        severity="HIGH",
        now=101,
    )

    assert first is not None
    assert second is None


def test_silence_blocks_incident():
    repo, service = build()
    repo.save_silence(
        SilenceRule(
            silence_id="s1",
            tenant_id="tenant-a",
            match_id="m1",
            trigger="MOMENTUM_SHIFT",
            starts_at=90,
            ends_at=120,
            reason="maintenance",
            created_by="ops",
        )
    )

    incident = service.open_incident(
        alert_id="a1",
        tenant_id="tenant-a",
        match_id="m1",
        trigger="MOMENTUM_SHIFT",
        severity="HIGH",
        now=100,
    )

    assert incident is None
