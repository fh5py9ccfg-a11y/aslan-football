import json

from apps.api.app.quorum_approval import (
    RedisQuorumApprovalRepository,
)

class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def set(self, key, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())

    def expire(self, key, ttl):
        return True

    def eval(self, script, number_of_keys, *args):
        request_key, votes_key, voter_key = args[:3]
        payload = args[4]
        voter = args[5]
        self.values[voter_key] = payload
        self.sets.setdefault(votes_key, set()).add(voter)
        return [1, payload]

def test_vote_integrity_detects_tampering():
    redis = Redis()
    repo = RedisQuorumApprovalRepository(
        redis,
        prefix="quorum",
        signing_secret="quorum-secret-at-least-sixteen",
    )
    repo.initialize(
        request_id="r1",
        required_approvals=1,
        required_groups=("admin",),
        expires_at=100,
    )
    repo.cast_vote(
        request_id="r1",
        voter="a",
        group="admin",
        approve=True,
        note="ok",
        now=10,
    )

    assert repo.verify_votes("r1") is True

    key = repo._voter_key("r1", "a")
    data = json.loads(redis.values[key])
    data["approve"] = False
    redis.values[key] = json.dumps(data)

    assert repo.verify_votes("r1") is False
