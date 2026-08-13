import asyncio

from apps.api.app.session_maintenance import (
    LeaseHeartbeat,
)

class FakeLease:
    def __init__(self, results):
        self.results = list(results)
        self.calls = 0

    def renew(self):
        self.calls += 1
        return self.results.pop(0)

def test_heartbeat_detects_lease_loss():
    async def scenario():
        lease = FakeLease([True, False])
        heartbeat = LeaseHeartbeat(
            lease=lease,
            interval_seconds=0.01,
        )
        await heartbeat.start()
        await asyncio.sleep(0.04)
        assert heartbeat.lost is True
        await heartbeat.stop()
        return lease.calls

    calls = asyncio.run(scenario())
    assert calls >= 2
