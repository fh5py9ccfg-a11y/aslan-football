import asyncio
import time

from apps.api.app.compensation_execution import (
    CompensationOwnershipLost,
)
from apps.api.app.compensation_execution_guard import (
    CompensationExecutionGuard,
)

class Record:
    compensation_id = "c1"

class Repository:
    def heartbeat(self, record):
        raise CompensationOwnershipLost(
            "taken over"
        )

def test_guard_stops_commit_after_ownership_loss():
    guard = CompensationExecutionGuard(
        repository=Repository(),
        heartbeat_interval_seconds=0.01,
    )

    result = asyncio.run(
        guard.run(
            record=Record(),
            operation=lambda: time.sleep(0.03),
        )
    )

    assert result.ownership_lost is True
    assert result.result is None
