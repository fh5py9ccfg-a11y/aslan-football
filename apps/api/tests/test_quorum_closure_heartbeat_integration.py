import asyncio
import time

from apps.api.app.quorum_closure import (
    QuorumQuarantineClosureService,
)
from apps.api.app.quorum_execution import (
    QuorumExecutionRecord,
)

class Request:
    claim_id = "c1"
    requested_by = "maker"

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
    def __init__(self):
        self.heartbeats = 0

    def claim(self, **kwargs):
        return True, QuorumExecutionRecord(
            request_id=kwargs["request_id"],
            claim_id=kwargs["claim_id"],
            status="IN_PROGRESS",
            owner=kwargs["owner"],
            owner_token="token",
            started_at=kwargs["now"],
            heartbeat_at=kwargs["now"],
            lease_expires_at=kwargs["now"] + 10,
            attempts=1,
            completed_at=None,
            result_status=None,
            reason=None,
        )

    def heartbeat(self, record):
        self.heartbeats += 1
        return record

    def complete(
        self,
        *,
        record,
        result_status,
        reason,
        now,
    ):
        return QuorumExecutionRecord(
            request_id=record.request_id,
            claim_id=record.claim_id,
            status="COMPLETED",
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
    def close(self, **kwargs):
        time.sleep(0.04)

        class Result:
            status = "CLOSED"
            reason = "healthy"

        return Result()

def test_closure_runs_with_heartbeat():
    execution = ExecutionRepo()
    service = QuorumQuarantineClosureService(
        approval_repository=ApprovalRepo(),
        quorum_repository=QuorumRepo(),
        closure_service=Closure(),
        execution_repository=execution,
        heartbeat_interval_seconds=0.01,
    )

    result = asyncio.run(
        service.vote_and_maybe_close_async(
            request_id="r1",
            voter="checker",
            group="admin",
            voter_roles=("admin",),
            approve=True,
            note="ok",
            fencing_token=7,
            now=100,
        )
    )

    assert result.closed is True
    assert execution.heartbeats >= 2
