import asyncio
import time

from apps.api.app.session_maintenance import (
    RedisSessionIndexMaintainer,
    SessionMaintenanceWorker,
)

class FakeRedis:
    def __init__(self):
        self.members = {
            "index": {f"session-{i}" for i in range(50)}
        }

    def scan(self, cursor, match, count):
        return 0, ["index"]

    def smembers(self, key):
        return set(self.members[key])

    def ttl(self, key):
        time.sleep(0.001)
        return 10

    def srem(self, key, value):
        return 1

    def expire(self, key, ttl):
        return 1

    def delete(self, key):
        return 1

class FakeLease:
    def __init__(self):
        self.renew_calls = 0

    def acquire(self):
        return True

    def renew(self):
        self.renew_calls += 1
        return self.renew_calls < 2

    def release(self):
        return True

def test_worker_aborts_after_lease_loss():
    async def scenario():
        worker = SessionMaintenanceWorker(
            maintainer=RedisSessionIndexMaintainer(
                FakeRedis()
            ),
            lease=FakeLease(),
            lease_heartbeat_seconds=0.01,
            interval_seconds=10,
            jitter_seconds=0,
        )
        return await worker.run_once()

    report = asyncio.run(scenario())

    assert report.lease_lost is True
    assert report.aborted is True
