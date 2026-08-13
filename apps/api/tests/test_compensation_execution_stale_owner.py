import json
import pytest

from apps.api.app.compensation_execution import (
    CompensationExecutionLease,
    CompensationOwnershipLost,
    RedisCompensationExecutionRepository,
)

class Redis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def eval(self, script, number_of_keys, *args):
        key = args[0]
        owner_token = args[1]
        payload = args[2]
        raw = self.values[key]
        current = json.loads(raw)
        if current["owner_token"] != owner_token:
            return [2, raw]
        self.values[key] = payload
        return [1, payload]

def test_stale_worker_cannot_complete():
    redis = Redis()
    repo = RedisCompensationExecutionRepository(
        redis,
        prefix="exec",
    )
    current = CompensationExecutionLease(
        compensation_id="c1",
        owner="w2",
        owner_token="token-2",
        status="IN_PROGRESS",
        claimed_at=11,
        heartbeat_at=11,
        lease_expires_at=71,
        attempts=2,
    )
    stale = CompensationExecutionLease(
        compensation_id="c1",
        owner="w1",
        owner_token="token-1",
        status="IN_PROGRESS",
        claimed_at=0,
        heartbeat_at=0,
        lease_expires_at=60,
        attempts=1,
    )
    redis.values["exec:c1"] = json.dumps(current.__dict__)

    with pytest.raises(CompensationOwnershipLost):
        repo.complete(stale)
