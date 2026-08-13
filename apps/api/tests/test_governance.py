from apps.api.app.governance import GovernanceService, RedisGovernanceRepository


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}
    def setex(self, key, ttl, value): self.values[key] = value
    def get(self, key): return self.values.get(key)
    def sadd(self, key, value): self.sets.setdefault(key, set()).add(value)
    def smembers(self, key): return self.sets.get(key, set())


def service():
    return GovernanceService(repository=RedisGovernanceRepository(Redis(), prefix="gov"))


def activate(item):
    item.create_policy(policy_id="p1", tenant_id="t1", name="Deployment", category="deployment", scope="prod", owner="ops", rules=("verified=true",), now=100)
    for idx, status in enumerate(("REVIEW", "APPROVED", "ACTIVE"), start=1):
        item.transition_policy(tenant_id="t1", policy_id="p1", version=1, target_status=status, now=100 + idx)


def test_policy_lifecycle_and_versioning():
    item = service()
    activate(item)
    v2 = item.version_policy(tenant_id="t1", policy_id="p1", rules=("verified=true", "rollback=true"), owner="ops", now=105)
    assert item.repository.get_policy(tenant_id="t1", policy_id="p1", version=1).status == "ACTIVE"
    assert v2.version == 2 and v2.status == "DRAFT"


def test_policy_evaluation():
    item = service()
    activate(item)
    ok = item.evaluate_policy(evaluation_id="e1", tenant_id="t1", policy_id="p1", resource="release:r1", facts={"verified": True}, evidence_ids=("ev1",), now=110)
    bad = item.evaluate_policy(evaluation_id="e2", tenant_id="t1", policy_id="p1", resource="release:r2", facts={"verified": False}, evidence_ids=(), now=111)
    assert ok.result == "COMPLIANT"
    assert bad.result == "NON_COMPLIANT" and len(bad.violations) == 1


def test_control_evidence_and_report():
    item = service()
    activate(item)
    item.create_control(control_id="c1", tenant_id="t1", name="Verified deployment", policy_ids=("p1",), required_evidence_types=("verification",), now=105)
    item.collect_evidence(evidence_id="ev1", tenant_id="t1", evidence_type="verification", source_system="deployment-verification", source_reference="session:v1", metadata={"status": "VERIFIED"}, now=106)
    report = item.compliance_report(tenant_id="t1", now=107)
    assert report["audit_readiness"] == "READY"
    assert report["compliant_controls"] == 1
