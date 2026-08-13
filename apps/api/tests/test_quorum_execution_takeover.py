import json

from apps.api.app.quorum_execution import (
    RedisQuorumExecutionRepository,
)

class Redis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def eval(self, script, number_of_keys, *args):
        key = args[0]

        if "lease_expires_at" in script and "existing_raw" in script:
            now = int(args[1])
            payload = args[2]
            existing = self.values.get(key)
            if existing is not None:
                data = json.loads(existing)
                if data["status"] == "COMPLETED":
                    return [0, existing]
                if int(data["lease_expires_at"]) > now:
                    return [0, existing]
            self.values[key] = payload
            return [1, payload]

        raise AssertionError("Unexpected script")

def test_expired_execution_can_be_taken_over():
    redis = Redis()
    repo = RedisQuorumExecutionRepository(
        redis,
        prefix="execution",
        lease_seconds=10,
    )

    created, first = repo.claim(
        request_id="r1",
        claim_id="c1",
        owner="owner-a",
        now=0,
    )
    assert created is True
    assert first.attempts == 1

    created, active = repo.claim(
        request_id="r1",
        claim_id="c1",
        owner="owner-b",
        now=5,
    )
    assert created is False
    assert active.owner == "owner-a"

    created, takeover = repo.claim(
        request_id="r1",
        claim_id="c1",
        owner="owner-b",
        now=11,
    )
    assert created is True
    assert takeover.owner == "owner-b"
    assert takeover.attempts == 2
