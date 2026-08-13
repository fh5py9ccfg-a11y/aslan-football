import asyncio
import time

from apps.api.app.compensation_execution import (
    CompensationOwnershipLost,
)
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
        self.completed = 0
        self.record = Record()

    def get(self, compensation_id):
        return self.record

    def mark_completed(self, record, now=None):
        self.completed += 1
        return record

class ExecutionRecord:
    compensation_id = "c1"
    status = "IN_PROGRESS"

class ExecutionRepository:
    def claim(self, **kwargs):
        return True, ExecutionRecord()

    def heartbeat(self, record):
        raise CompensationOwnershipLost("taken over")

    def complete(self, record):
        raise AssertionError("complete should not run")

def test_ownership_loss_prevents_business_commit():
    registry = CompensationHandlerRegistry()
    registry.register(
        "ACTION",
        lambda record: time.sleep(0.03),
    )
    repository = Repository()
    orchestrator = CompensationOrchestrator(
        repository=repository,
        registry=registry,
        execution_repository=ExecutionRepository(),
        heartbeat_interval_seconds=0.01,
    )

    result = asyncio.run(
        orchestrator.execute_async(
            "c1",
            now=100,
        )
    )

    assert result.status == "OWNERSHIP_LOST"
    assert result.ownership_lost is True
    assert repository.completed == 0
