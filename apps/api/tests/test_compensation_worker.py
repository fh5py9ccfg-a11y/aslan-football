import asyncio

from apps.api.app.compensation_orchestrator import (
    CompensationExecutionResult,
    CompensationWorker,
)

class Record:
    compensation_id = "c1"

class Repository:
    def list_due(self, limit):
        return (Record(),)

class Orchestrator:
    def execute(self, compensation_id):
        return CompensationExecutionResult(
            compensation_id=compensation_id,
            status="COMPLETED",
            attempts=1,
            next_attempt_at=None,
            error=None,
            completed_at=100,
        )

def test_worker_processes_due_records():
    worker = CompensationWorker(
        repository=Repository(),
        orchestrator=Orchestrator(),
        interval_seconds=10,
        batch_size=5,
    )

    results = asyncio.run(
        worker.run_once()
    )

    assert len(results) == 1
    assert results[0].status == "COMPLETED"
