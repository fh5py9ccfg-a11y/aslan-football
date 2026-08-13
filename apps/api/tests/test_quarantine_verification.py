from apps.api.app.quarantine_verification import (
    QuarantineVerificationService,
)

class Diagnostic:
    def __init__(
        self,
        *,
        orphans,
        live,
        ttl,
        members,
        error=None,
    ):
        self.claim_id = "c1"
        self.index_key = "index-a"
        self.phase = "subject"
        self.orphan_members = orphans
        self.live_members = live
        self.index_ttl = ttl
        self.member_count = members
        self.error = error

class Diagnostics:
    def __init__(self):
        self.calls = 0

    def inspect(self, claim_id, now=None):
        self.calls += 1
        if self.calls == 1:
            return Diagnostic(
                orphans=2,
                live=1,
                ttl=-1,
                members=3,
            )
        return Diagnostic(
            orphans=0,
            live=1,
            ttl=120,
            members=1,
        )

class Retry:
    def retry(self, claim_id, now=None):
        class Result:
            status = "SUCCEEDED"
        return Result()

class EvidenceRepo:
    def __init__(self):
        self.item = None

    def get(self, claim_id):
        return self.item

    def save(self, evidence):
        self.item = evidence

def test_retry_and_verify_creates_health_evidence():
    repo = EvidenceRepo()
    service = QuarantineVerificationService(
        diagnostic_service=Diagnostics(),
        retry_service=Retry(),
        evidence_repository=repo,
    )

    evidence = service.retry_and_verify(
        claim_id="c1",
        operator="admin",
        fencing_token=7,
        now=100,
    )

    assert evidence.verified is True
    assert evidence.pre_orphans == 2
    assert evidence.post_orphans == 0
    assert evidence.post_ttl == 120
    assert repo.item == evidence
