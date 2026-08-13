import json
import pytest

from apps.api.app.quarantine_approval import (
    ApprovalConflict,
    ApprovalExpired,
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
        raw = self.values.get(key)
        if raw is None:
            return [0, "missing"]
        current = json.loads(raw)
        if current["status"] != "PENDING":
            return [2, raw]
        if int(current["expires_at"]) <= int(now):
            current["status"] = "EXPIRED"
            encoded = json.dumps(current)
            self.values[key] = encoded
            return [3, encoded]
        self.values[key] = payload
        return [1, payload]

def repository():
    return RedisQuarantineApprovalRepository(
        FakeRedis(),
        prefix="approval",
        ttl_seconds=10,
        signing_secret="approval-secret-at-least-sixteen",
    )

def test_maker_checker_and_idempotent_decision():
    repo = repository()
    item = repo.create(
        claim_id="c1",
        requested_by="maker",
        note="close it",
        now=0,
    )

    with pytest.raises(ApprovalConflict):
        repo.decide(
            request_id=item.request_id,
            decided_by="maker",
            approve=True,
            decision_note="self approve",
            now=1,
        )

    decided = repo.decide(
        request_id=item.request_id,
        decided_by="checker",
        approve=True,
        decision_note="approved",
        now=2,
    )
    again = repo.decide(
        request_id=item.request_id,
        decided_by="checker",
        approve=True,
        decision_note="duplicate",
        now=3,
    )

    assert decided.status == "APPROVED"
    assert again.record_hash == decided.record_hash

def test_expired_request_rejected():
    repo = repository()
    item = repo.create(
        claim_id="c1",
        requested_by="maker",
        note="close it",
        now=0,
    )

    with pytest.raises(ApprovalExpired):
        repo.decide(
            request_id=item.request_id,
            decided_by="checker",
            approve=True,
            decision_note="late",
            now=11,
        )
