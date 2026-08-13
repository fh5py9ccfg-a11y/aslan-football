from apps.api.app.quarantine_verification import (
    QuarantineVerificationService,
)

class Diagnostic:
    claim_id = "c1"
    index_key = "index-a"
    phase = "subject"
    orphan_members = 1
    live_members = 0
    index_ttl = -1
    member_count = 1
    error = None

class Diagnostics:
    def inspect(self, claim_id, now=None):
        return Diagnostic()

class Retry:
    def retry(self, claim_id, now=None):
        class Result:
            status = "FAILED"
        return Result()

class Repo:
    def get(self, claim_id):
        return None

    def save(self, evidence):
        self.evidence = evidence

def test_failed_retry_does_not_verify():
    service = QuarantineVerificationService(
        diagnostic_service=Diagnostics(),
        retry_service=Retry(),
        evidence_repository=Repo(),
    )

    evidence = service.retry_and_verify(
        claim_id="c1",
        operator="ops",
        fencing_token=3,
        now=100,
    )

    assert evidence.verified is False
    assert evidence.reason == "Retry başarısız"
