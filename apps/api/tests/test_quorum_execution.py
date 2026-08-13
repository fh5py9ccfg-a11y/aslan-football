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

        if "existing.owner_token" in script:
            owner_token = args[1]
            payload = args[2]
            raw = self.values.get(key)
            if raw is None:
                return [0, "missing"]
            current = json.loads(raw)
            if current["owner_token"] != owner_token:
                return [2, raw]
            if current["status"] == "COMPLETED":
                return [3, raw]
            self.values[key] = payload
            return [1, payload]

        if "existing_raw" in script:
            now = int(args[1])
            payload = args[2]
            raw = self.values.get(key)
            if raw is not None:
                current = json.loads(raw)
                if current["status"] == "COMPLETED":
                    return [0, raw]
                if int(current["lease_expires_at"]) > now:
                    return [0, raw]
            self.values[key] = payload
            return [1, payload]

        raise AssertionError("Unexpected script")

def test_execution_claim_and_complete_are_durable():
    redis = Redis()
    repo = RedisQuorumExecutionRepository(
        redis,
        prefix="execution",
        lease_seconds=60,
    )

    created, record = repo.claim(
        request_id="r1",
        claim_id="c1",
        owner="checker",
        now=10,
    )
    assert created is True
    assert record.status == "IN_PROGRESS"
    assert record.owner_token

    created_again, same = repo.claim(
        request_id="r1",
        claim_id="c1",
        owner="other",
        now=11,
    )
    assert created_again is False
    assert same.owner == "checker"

    completed = repo.complete(
        record=record,
        result_status="CLOSED",
        reason="healthy",
        now=12,
    )
    assert completed.status == "COMPLETED"

    loaded = repo.get("r1")
    assert loaded is not None
    assert loaded.result_status == "CLOSED"
