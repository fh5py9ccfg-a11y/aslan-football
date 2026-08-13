from dataclasses import dataclass

from apps.api.app.idempotent_closure import (
    IdempotentClosureExecutor,
)

@dataclass
class Result:
    status: str
    reason: str

class Effects:
    def __init__(self):
        self.record = None

    def claim(self, **kwargs):
        if self.record is None:
            class Record:
                key = kwargs["key"]
                operation = kwargs["operation"]
                owner = kwargs["owner"]
                status = "IN_PROGRESS"
                result_payload = None
                error = None
            self.record = Record()
            return True, self.record
        return False, self.record

    def complete(self, *, record, result_payload):
        record.status = "COMPLETED"
        record.result_payload = result_payload

    def fail(self, *, record, error):
        record.status = "FAILED"
        record.error = error

class Compensations:
    def __init__(self):
        self.created = 0

    def create(self, **kwargs):
        self.created += 1
        class Record:
            compensation_id = "comp-1"
        return Record()

def test_success_is_replayed_without_second_operation():
    effects = Effects()
    executor = IdempotentClosureExecutor(
        effect_repository=effects,
        compensation_repository=Compensations(),
    )
    calls = {"count": 0}

    def operation():
        calls["count"] += 1
        return Result("CLOSED", "healthy")

    first = executor.execute(
        request_id="r1",
        claim_id="c1",
        owner="owner",
        operation=operation,
    )
    second = executor.execute(
        request_id="r1",
        claim_id="c1",
        owner="other",
        operation=operation,
    )

    assert first.replayed is False
    assert second.replayed is True
    assert calls["count"] == 1

def test_failure_creates_compensation():
    comps = Compensations()
    executor = IdempotentClosureExecutor(
        effect_repository=Effects(),
        compensation_repository=comps,
    )

    result = executor.execute(
        request_id="r1",
        claim_id="c1",
        owner="owner",
        operation=lambda: (_ for _ in ()).throw(
            RuntimeError("partial failure")
        ),
    )

    assert result.status == "FAILED"
    assert result.payload["compensation_id"] == "comp-1"
    assert comps.created == 1
