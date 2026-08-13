from apps.api.app.compensation_orchestrator import (
    CompensationHandlerRegistry,
    CompensationOrchestrator,
)

class Record:
    compensation_id = "c1"
    action = "ACTION"
    status = "RETRY_SCHEDULED"
    reason = ""
    attempts = 2
    completed_at = None
    next_attempt_at = 0

class Repository:
    def get(self, compensation_id):
        return Record()

    def mark_dead_letter(self, record, reason, now=None):
        record.status = "DEAD_LETTER"
        record.reason = reason
        record.attempts += 1
        record.completed_at = now
        return record

def test_max_attempts_moves_to_dead_letter():
    registry = CompensationHandlerRegistry()
    registry.register(
        "ACTION",
        lambda record: (_ for _ in ()).throw(
            RuntimeError("permanent")
        ),
    )
    orchestrator = CompensationOrchestrator(
        repository=Repository(),
        registry=registry,
        max_attempts=3,
        base_backoff_seconds=10,
    )

    result = orchestrator.execute("c1", now=100)

    assert result.status == "DEAD_LETTER"
    assert result.attempts == 3
