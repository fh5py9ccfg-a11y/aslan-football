from apps.api.app.quorum_closure import (
    QuorumQuarantineClosureService,
)
from apps.api.app.quorum_execution import (
    QuorumExecutionRecord,
)

class Request:
    request_id = "r1"
    claim_id = "c1"
    requested_by = "maker"
    expires_at = 100

class ApprovalRepo:
    def get(self, request_id):
        return Request()

class Decision:
    status = "APPROVED"
    approvals = 2
    rejections = 0
    groups = ("admin", "security")

class QuorumRepo:
    def cast_vote(self, **kwargs):
        pass

    def decision(self, request_id):
        return Decision()

class ExecutionRepo:
    def claim(self, **kwargs):
        return False, QuorumExecutionRecord(
            request_id="r1",
            claim_id="c1",
            status="COMPLETED",
            owner="first-checker",
            owner_token="token-first",
            started_at=1,
            heartbeat_at=1,
            lease_expires_at=61,
            attempts=1,
            completed_at=2,
            result_status="CLOSED",
            reason="already done",
        )

class Closure:
    def close(self, **kwargs):
        raise AssertionError("closure must not execute twice")

def test_completed_execution_survives_process_restart():
    service = QuorumQuarantineClosureService(
        approval_repository=ApprovalRepo(),
        quorum_repository=QuorumRepo(),
        closure_service=Closure(),
        execution_repository=ExecutionRepo(),
    )

    result = service.vote_and_maybe_close(
        request_id="r1",
        voter="second-checker",
        group="admin",
        voter_roles=("admin",),
        approve=True,
        note="ok",
        fencing_token=9,
        now=10,
    )

    assert result.closed is True
    assert result.reason == "already done"
