from apps.api.app.quorum_risk_policy import (
    QuorumRiskPolicyEngine,
)

def test_low_risk_requires_single_admin():
    policy = QuorumRiskPolicyEngine().evaluate(
        orphan_members=0,
        live_members=0,
        index_ttl=-2,
        attempts=1,
        phase="subject",
    )
    assert policy.level == "LOW"
    assert policy.required_approvals == 1
    assert policy.required_groups == ("admin",)

def test_critical_risk_requires_three_groups():
    policy = QuorumRiskPolicyEngine().evaluate(
        orphan_members=150,
        live_members=1500,
        index_ttl=-1,
        attempts=5,
        phase="family",
    )
    assert policy.level == "CRITICAL"
    assert policy.required_approvals == 3
    assert policy.required_groups == (
        "admin",
        "security",
        "ops",
    )
