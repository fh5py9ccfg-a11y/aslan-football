from dataclasses import dataclass

from apps.api.app.continuous_compliance import (
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


@dataclass
class GovernanceReport:
    policy_coverage_percent: float
    evidence_coverage_percent: float
    total_controls: int
    compliant_controls: int
    gaps: tuple[str, ...]


class Governance:
    def __init__(
        self,
        *,
        policy=100,
        evidence=100,
        total=1,
        compliant=1,
        gaps=(),
    ):
        self.report = GovernanceReport(
            policy,
            evidence,
            total,
            compliant,
            gaps,
        )

    def compliance_report(self, **kwargs):
        return self.report


class ExceptionRepository:
    def list_exceptions(self, tenant_id):
        return ()


class Exceptions:
    repository = ExceptionRepository()

    def framework_report(
        self,
        *,
        tenant_id,
        framework,
        now=None,
    ):
        return {
            "framework": framework,
            "total_controls": 1,
            "coverage_percent": 100.0,
            "gaps": [],
        }

    def exception_status(self, **kwargs):
        raise AssertionError


def build(governance=None):
    return ContinuousComplianceService(
        repository=(
            RedisContinuousComplianceRepository(
                Redis(),
                prefix="cc",
            )
        ),
        governance_service=(
            governance or Governance()
        ),
        governance_exception_service=Exceptions(),
    )


def test_healthy_snapshot():
    service = build()
    snapshot = service.monitor(
        snapshot_id="s1",
        tenant_id="t1",
        now=100,
    )

    assert snapshot.overall_score == 100
    assert snapshot.status == "HEALTHY"
    assert snapshot.gaps == ()


def test_score_drop_creates_drift():
    service = build()
    service.monitor(
        snapshot_id="s1",
        tenant_id="t1",
        now=100,
    )
    service.governance_service = Governance(
        policy=50,
        evidence=50,
        total=2,
        compliant=1,
        gaps=("control gap",),
    )
    second = service.monitor(
        snapshot_id="s2",
        tenant_id="t1",
        now=200,
    )
    drifts = service.repository.list_drifts(
        "t1"
    )

    assert second.overall_score < 100
    assert any(
        item.drift_type == "SCORE_DROP"
        for item in drifts
    )
    assert any(
        item.drift_type == "NEW_GAP"
        for item in drifts
    )
