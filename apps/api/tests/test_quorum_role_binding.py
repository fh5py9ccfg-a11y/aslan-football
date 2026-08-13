import pytest

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

class QuorumRepo:
    def cast_vote(self, **kwargs):
        raise AssertionError("vote should not be cast")

class ExecutionRepo:
    pass

class Closure:
    pass

def test_vote_group_must_match_verified_role():
    service = QuorumQuarantineClosureService(
        approval_repository=ApprovalRepo(),
        quorum_repository=QuorumRepo(),
        closure_service=Closure(),
        execution_repository=ExecutionRepo(),
    )

    with pytest.raises(ValueError):
        service.vote_and_maybe_close(
            request_id="r1",
            voter="checker",
            group="security",
            voter_roles=("admin",),
            approve=True,
            note="ok",
            fencing_token=7,
            now=10,
        )
