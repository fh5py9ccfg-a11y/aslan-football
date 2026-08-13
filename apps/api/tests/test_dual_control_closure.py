from apps.api.app.dual_control_closure import (
    DualControlQuarantineClosureService,
)

class Approval:
    def __init__(self, status):
        self.request_id = "r1"
        self.claim_id = "c1"
        self.status = status
        self.decided_by = "checker"
        self.decision_note = "decision"

class Repository:
    def __init__(self, status="APPROVED"):
        self.status = status

    def create(self, **kwargs):
        class Request:
            request_id = "r1"
            claim_id = kwargs["claim_id"]
            requested_by = kwargs["requested_by"]
        return Request()

    def decide(self, **kwargs):
        return Approval(
            "APPROVED" if kwargs["approve"] else "REJECTED"
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

def test_approved_request_executes_closure():
    closure = Closure()
    service = DualControlQuarantineClosureService(
        approval_repository=Repository(),
        closure_service=closure,
    )

    result = service.decide_and_close(
        request_id="r1",
        decided_by="checker",
        approve=True,
        decision_note="approved",
        fencing_token=7,
        now=100,
    )

    assert result.closed is True
    assert result.closure_status == "CLOSED"
    assert closure.calls == 1

def test_rejected_request_does_not_execute_closure():
    closure = Closure()
    service = DualControlQuarantineClosureService(
        approval_repository=Repository(),
        closure_service=closure,
    )

    result = service.decide_and_close(
        request_id="r1",
        decided_by="checker",
        approve=False,
        decision_note="rejected",
        fencing_token=0,
        now=100,
    )

    assert result.closed is False
    assert result.closure_status == "NOT_EXECUTED"
    assert closure.calls == 0
