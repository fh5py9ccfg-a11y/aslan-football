import asyncio
import time

from apps.api.app.compensation_orchestrator import (
    CompensationHandlerRegistry,
    CompensationOrchestrator,
)

class Record:
    compensation_id = "c1"
    action = "ACTION"
    status = "PENDING"
    reason = ""
    attempts = 0
    completed_at = None
    next_attempt_at = 0

class Repository:
    def __init__(self):
        self.record = Record()
        self.completed = 0

    def get(self, compensation_id):
        return self.record

    def mark_completed(self, record, now=None):
        self.completed += 1
        record.status = "COMPLETED"
        record.attempts += 1
        record.completed_at = now
        return record

class ExecutionRecord:
    compensation_id = "c1"
    status = "IN_PROGRESS"

class ExecutionRepository:
    def __init__(self):
        self.heartbeats = 0
        self.completed = 0

    def claim(self, **kwargs):
        return True, ExecutionRecord()

    def heartbeat(self, record):
        self.heartbeats += 1
        return record

    def complete(self, record):
        self.completed += 1
        return record

def test_orchestrator_keeps_execution_alive():
    registry = CompensationHandlerRegistry()
    registry.register(
        "ACTION",
        lambda record: time.sleep(0.04),
    )
    execution = ExecutionRepository()
    repository = Repository()
    orchestrator = CompensationOrchestrator(
        repository=repository,
        registry=registry,
        execution_repository=execution,
        heartbeat_interval_seconds=0.01,
    )

    result = asyncio.run(
        orchestrator.execute_async(
            "c1",
            now=100,
        )
    )

    assert result.status == "COMPLETED"
    assert execution.heartbeats >= 2
    assert execution.completed == 1
    assert repository.completed == 1
