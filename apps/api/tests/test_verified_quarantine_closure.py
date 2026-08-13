from apps.api.app.quarantine_closure import (
    VerifiedQuarantineClosureService,
)

class Evidence:
    verified = True
    reason = "Retry sonrası indeks sağlıklı"

class Verification:
    def retry_and_verify(self, **kwargs):
        return Evidence()

class Manager:
    def __init__(self):
        self.releases = 0
        self.requeues = 0

    def release(self, **kwargs):
        self.releases += 1
        class Action:
            index_key = "index-a"
            phase = "subject"
            fencing_token = 5
        return Action()

    def requeue(self, **kwargs):
        self.requeues += 1

def test_verified_closure_releases_and_requeues():
    manager = Manager()
    service = VerifiedQuarantineClosureService(
        verification_service=Verification(),
        quarantine_manager=manager,
        progress_repository=object(),
    )

    result = service.close(
        claim_id="c1",
        operator="admin",
        note="verified",
        fencing_token=5,
        now=100,
    )

    assert result.status == "CLOSED"
    assert result.verified is True
    assert result.released is True
    assert manager.releases == 1
    assert manager.requeues == 1

class HeldEvidence:
    verified = False
    reason = "Orphan üyeler temizlenmedi"

class HeldVerification:
    def retry_and_verify(self, **kwargs):
        return HeldEvidence()

def test_unverified_closure_is_held():
    manager = Manager()
    service = VerifiedQuarantineClosureService(
        verification_service=HeldVerification(),
        quarantine_manager=manager,
        progress_repository=object(),
    )

    result = service.close(
        claim_id="c1",
        operator="ops",
        note="not healthy",
        fencing_token=5,
        now=100,
    )

    assert result.status == "HELD"
    assert result.released is False
    assert manager.releases == 0
