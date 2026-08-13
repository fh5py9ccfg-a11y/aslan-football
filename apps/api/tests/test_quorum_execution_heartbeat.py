import asyncio

from apps.api.app.quorum_execution_heartbeat import (
    QuorumExecutionHeartbeat,
)

class Record:
    request_id = "r1"

class Repository:
    def __init__(self):
        self.calls = 0

    def heartbeat(self, record):
        self.calls += 1
        return record

def test_execution_heartbeat_renews_record():
    async def scenario():
        repo = Repository()
        heartbeat = QuorumExecutionHeartbeat(
            repository=repo,
            record=Record(),
            interval_seconds=0.01,
        )
        await heartbeat.start()
        await asyncio.sleep(0.035)
        await heartbeat.stop()
        return repo.calls

    assert asyncio.run(scenario()) >= 2
