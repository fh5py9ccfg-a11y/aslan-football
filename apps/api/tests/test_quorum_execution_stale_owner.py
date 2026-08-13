import json
import pytest

from apps.api.app.quorum_execution import (
    ExecutionOwnershipLost,
    RedisQuorumExecutionRepository,
)

class Redis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def eval(self, script, number_of_keys, *args):
        key = args[0]
        if "existing.owner_token" in script:
            owner_token = args[1]
            payload = args[2]
            existing = json.loads(self.values[key])
            if existing["owner_token"] != owner_token:
                return [2, self.values[key]]
            self.values[key] = payload
            return [1, payload]
        raise AssertionError("Unexpected script")

def test_stale_owner_cannot_complete_after_takeover():
    redis = Redis()
    repo = RedisQuorumExecutionRepository(
        redis,
        prefix="execution",
    )

    from apps.api.app.quorum_execution import QuorumExecutionRecord

    stale = QuorumExecutionRecord(
        request_id="r1",
        claim_id="c1",
        status="IN_PROGRESS",
        owner="owner-a",
        owner_token="token-a",
        started_at=0,
        heartbeat_at=0,
        lease_expires_at=10,
        attempts=1,
        completed_at=None,
        result_status=None,
        reason=None,
    )
    current = QuorumExecutionRecord(
        request_id="r1",
        claim_id="c1",
        status="IN_PROGRESS",
        owner="owner-b",
        owner_token="token-b",
        started_at=11,
        heartbeat_at=11,
        lease_expires_at=21,
        attempts=2,
        completed_at=None,
        result_status=None,
        reason=None,
    )
    redis.values["execution:r1"] = json.dumps(
        current.__dict__
    )

    with pytest.raises(ExecutionOwnershipLost):
        repo.complete(
            record=stale,
            result_status="CLOSED",
            reason="late",
            now=12,
        )
