import json

from apps.api.app.compensation_execution import (
    RedisCompensationExecutionRepository,
)

class Redis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def eval(self, script, number_of_keys, *args):
        key = args[0]

        if "existing_raw" in script:
            now = int(args[1])
            payload = args[2]
            raw = self.values.get(key)
            if raw:
                current = json.loads(raw)
                if current["status"] == "COMPLETED":
                    return [0, raw]
                if current["lease_expires_at"] > now:
                    return [0, raw]
            self.values[key] = payload
            return [1, payload]

        if "existing.owner_token" in script:
            owner_token = args[1]
            payload = args[2]
            raw = self.values[key]
            current = json.loads(raw)
            if current["owner_token"] != owner_token:
                return [2, raw]
            self.values[key] = payload
            return [1, payload]

        raise AssertionError("Unexpected script")

def test_claim_complete_and_replay():
    redis = Redis()
    repo = RedisCompensationExecutionRepository(
        redis,
        prefix="exec",
        lease_seconds=10,
    )

    created, record = repo.claim(
        compensation_id="c1",
        owner="w1",
        now=0,
    )
    assert created is True

    created, active = repo.claim(
        compensation_id="c1",
        owner="w2",
        now=5,
    )
    assert created is False
    assert active.owner == "w1"

    completed = repo.complete(record)
    assert completed.status == "COMPLETED"

    created, replay = repo.claim(
        compensation_id="c1",
        owner="w3",
        now=20,
    )
    assert created is False
    assert replay.status == "COMPLETED"
