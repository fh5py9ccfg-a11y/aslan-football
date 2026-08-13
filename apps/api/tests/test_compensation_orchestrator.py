from apps.api.app.compensation_orchestrator import (
    CompensationHandlerRegistry,
    CompensationOrchestrator,
)

class Record:
    compensation_id = "c1"
    request_id = "r1"
    claim_id = "q1"
    action = "ACTION"
    status = "PENDING"
    reason = ""
    attempts = 0
    completed_at = None
    next_attempt_at = 0

class Repository:
    def __init__(self):
        self.record = Record()

    def get(self, compensation_id):
        return self.record

    def mark_completed(self, record, now=None):
        record.status = "COMPLETED"
        record.attempts += 1
        record.completed_at = now
        return record

    def schedule_retry(self, record, reason, next_attempt_at):
        record.status = "RETRY_SCHEDULED"
        record.reason = reason
        record.attempts += 1
        record.next_attempt_at = next_attempt_at
        return record

    def mark_dead_letter(self, record, reason, now=None):
        record.status = "DEAD_LETTER"
        record.reason = reason
        record.attempts += 1
        record.completed_at = now
        return record

def test_successful_compensation_completes():
    registry = CompensationHandlerRegistry()
    calls = {"count": 0}
    registry.register(
        "ACTION",
        lambda record: calls.__setitem__(
            "count",
            calls["count"] + 1,
        ),
    )
    orchestrator = CompensationOrchestrator(
        repository=Repository(),
        registry=registry,
        max_attempts=3,
        base_backoff_seconds=10,
    )

    result = orchestrator.execute("c1", now=100)

    assert result.status == "COMPLETED"
    assert result.attempts == 1
    assert calls["count"] == 1

def test_failure_schedules_exponential_retry():
    registry = CompensationHandlerRegistry()
    registry.register(
        "ACTION",
        lambda record: (_ for _ in ()).throw(
            RuntimeError("boom")
        ),
    )
    orchestrator = CompensationOrchestrator(
        repository=Repository(),
        registry=registry,
        max_attempts=3,
        base_backoff_seconds=10,
    )

    result = orchestrator.execute("c1", now=100)

    assert result.status == "RETRY_SCHEDULED"
    assert result.next_attempt_at == 110
