import asyncio
import time

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
        return record

def test_guard_keeps_heartbeat_alive_during_operation():
    repo = Repository()
    guard = QuorumExecutionGuard(
        repository=repo,
        heartbeat_interval_seconds=0.01,
    )

    result = asyncio.run(
        guard.run(
            record=Record(),
            operation=lambda: (
                time.sleep(0.04)
                or "done"
            ),
        )
    )

    assert result.result == "done"
    assert result.ownership_lost is False
    assert repo.calls >= 2
