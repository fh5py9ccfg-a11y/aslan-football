from apps.api.app.continuous_compliance import (
    ComplianceDriftEvent,
    ContinuousComplianceService,
    RedisContinuousComplianceRepository,
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


class Dependency:
    pass


def test_remediation_lifecycle():
    repository = RedisContinuousComplianceRepository(
        Redis(),
        prefix="cc",
    )
    repository.save_drift(
        ComplianceDriftEvent(
            drift_id="d1",
            tenant_id="t1",
            drift_type="NEW_GAP",
            severity="MEDIUM",
            resource="control:c1",
            detail="Missing evidence",
            previous_value=None,
            current_value="missing",
            detected_at=100,
        )
    )
    service = ContinuousComplianceService(
        repository=repository,
        governance_service=Dependency(),
        governance_exception_service=Dependency(),
    )

    action = service.create_remediation(
        action_id="a1",
        tenant_id="t1",
        drift_id="d1",
        action_type="COLLECT_EVIDENCE",
        assignee="ops-user",
        due_at=200,
        detail="Collect verification evidence",
        now=101,
    )
    in_progress = service.transition_remediation(
        action_id="a1",
        target_status="IN_PROGRESS",
        now=102,
    )
    resolved = service.transition_remediation(
        action_id="a1",
        target_status="RESOLVED",
        now=103,
    )

    assert action.status == "OPEN"
    assert in_progress.status == "IN_PROGRESS"
    assert resolved.status == "RESOLVED"
