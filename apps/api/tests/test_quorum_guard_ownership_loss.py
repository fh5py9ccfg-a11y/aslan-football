import asyncio
import time

from apps.api.app.quorum_execution import (
    ExecutionOwnershipLost,
)
from apps.api.app.quorum_execution_guard import (
    QuorumExecutionGuard,
)

class Record:
    request_id = "r1"
    owner_token = "token"

class Repository:
    def __init__(self):
        self.calls = 0

    def heartbeat(self, record):
        self.calls += 1
        raise ExecutionOwnershipLost(
            "taken over"
        )

def test_guard_marks_ownership_loss():
    guard = QuorumExecutionGuard(
        repository=Repository(),
        heartbeat_interval_seconds=0.01,
    )

    result = asyncio.run(
        guard.run(
            record=Record(),
            operation=lambda: (
                time.sleep(0.03)
                or "done"
            ),
        )
    )

    assert result.result is None
    assert result.ownership_lost is True
