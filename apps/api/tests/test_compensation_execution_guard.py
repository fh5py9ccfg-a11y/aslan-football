import asyncio
import time

from apps.api.app.compensation_execution_guard import (
    CompensationExecutionGuard,
)

class Record:
    compensation_id = "c1"

class Repository:
    def __init__(self):
        self.calls = 0

    def heartbeat(self, record):
        self.calls += 1
        return record

def test_guard_renews_during_long_handler():
    repo = Repository()
    guard = CompensationExecutionGuard(
        repository=repo,
        heartbeat_interval_seconds=0.01,
    )

    result = asyncio.run(
        guard.run(
            record=Record(),
            operation=lambda: time.sleep(0.04),
        )
    )

    assert result.ownership_lost is False
    assert result.error is None
    assert repo.calls >= 2
