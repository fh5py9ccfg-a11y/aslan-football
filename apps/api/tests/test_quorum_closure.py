from apps.api.app.quorum_closure import (
    QuorumQuarantineClosureService,
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
    def __init__(self, status, approvals):
        self.status = status
        self.approvals = approvals
        self.rejections = 0
        self.groups = ("admin", "security")
        self.quorum_met = status == "APPROVED"
        self.rejected = False

class QuorumRepo:
    def __init__(self):
        self.votes = 0

    def initialize(self, **kwargs):
        return kwargs

    def cast_vote(self, **kwargs):
        self.votes += 1

    def decision(self, request_id):
        return Decision(
            "APPROVED" if self.votes >= 2 else "PENDING",
            self.votes,
        )

class Execution:
    def __init__(self):
        self.record = None

    def claim(self, **kwargs):
        from apps.api.app.quorum_execution import QuorumExecutionRecord
        self.record = QuorumExecutionRecord(
            request_id=kwargs['request_id'],
            claim_id=kwargs['claim_id'],
            status='IN_PROGRESS',
            owner=kwargs['owner'],
            owner_token='test-owner-token',
            started_at=kwargs['now'],
            heartbeat_at=kwargs['now'],
            lease_expires_at=kwargs['now'] + 60,
            attempts=1,
            completed_at=None,
            result_status=None,
            reason=None,
        )
        return True, self.record

    def complete(self, *, record, result_status, reason, now):
        from apps.api.app.quorum_execution import QuorumExecutionRecord
        return QuorumExecutionRecord(
            request_id=record.request_id,
            claim_id=record.claim_id,
            status='COMPLETED',
            owner=record.owner,
            owner_token=record.owner_token,
            started_at=record.started_at,
            heartbeat_at=record.heartbeat_at,
            lease_expires_at=record.lease_expires_at,
            attempts=record.attempts,
            completed_at=now,
            result_status=result_status,
            reason=reason,
        )

class Closure:
    def __init__(self):
        self.calls = 0

    def close(self, **kwargs):
        self.calls += 1
        class Result:
            status = "CLOSED"
            reason = "healthy"
        return Result()

def test_closure_runs_once_after_quorum():
    quorum = QuorumRepo()
    closure = Closure()
    service = QuorumQuarantineClosureService(
        approval_repository=ApprovalRepo(),
        quorum_repository=quorum,
        closure_service=closure,
        execution_repository=Execution(),
    )

    first = service.vote_and_maybe_close(
        request_id="r1",
        voter="checker-a",
        group="admin",
        voter_roles=("admin",),
        approve=True,
        note="ok",
        fencing_token=7,
        now=10,
    )
    assert first.closed is False

    second = service.vote_and_maybe_close(
        request_id="r1",
        voter="checker-b",
        group="security",
        voter_roles=("security",),
        approve=True,
        note="ok",
        fencing_token=7,
        now=11,
    )
    assert second.closed is True
    assert closure.calls == 1
