import json

from apps.api.app.quarantine_approval import (
    RedisQuarantineApprovalRepository,
)

class FakeRedis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def set(self, key, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def expire(self, key, ttl):
        return True

    def smembers(self, key):
        return self.sets.get(key, set())

    def eval(self, script, number_of_keys, key, now, payload):
        self.values[key] = payload
        return [1, payload]

def test_chain_verification_detects_tampering():
    redis = FakeRedis()
    repo = RedisQuarantineApprovalRepository(
        redis,
        prefix="approval",
        ttl_seconds=30,
        signing_secret="approval-secret-at-least-sixteen",
    )

    first = repo.create(
        claim_id="c1",
        requested_by="maker-a",
        note="first",
        now=1,
    )
    second = repo.create(
        claim_id="c1",
        requested_by="maker-b",
        note="second",
        now=2,
    )

    assert repo.verify_chain("c1") is True

    key = repo._request_key(first.request_id)
    data = json.loads(redis.values[key])
    data["note"] = "tampered"
    redis.values[key] = json.dumps(data)

    assert repo.verify_chain("c1") is False
