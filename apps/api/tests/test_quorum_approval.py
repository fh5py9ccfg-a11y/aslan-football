import json
import pytest

from apps.api.app.quorum_approval import (
    DuplicateVote,
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
        now = int(args[3])
        payload = args[4]
        voter = args[5]
        request = json.loads(self.values[request_key])

        if now >= int(request["expires_at"]):
            return [3, "expired"]
        if voter_key in self.values:
            return [2, self.values[voter_key]]

        self.values[voter_key] = payload
        self.sets.setdefault(votes_key, set()).add(voter)
        return [1, payload]

def repository():
    redis = Redis()
    repo = RedisQuorumApprovalRepository(
        redis,
        prefix="quorum",
        signing_secret="quorum-secret-at-least-sixteen",
    )
    repo.initialize(
        request_id="r1",
        required_approvals=2,
        required_groups=("admin", "security"),
        expires_at=100,
    )
    return redis, repo

def test_quorum_requires_count_and_groups():
    _, repo = repository()
    repo.cast_vote(
        request_id="r1",
        voter="a",
        group="admin",
        approve=True,
        note="ok",
        now=10,
    )
    assert repo.decision("r1").status == "PENDING"

    repo.cast_vote(
        request_id="r1",
        voter="b",
        group="security",
        approve=True,
        note="ok",
        now=11,
    )
    decision = repo.decision("r1")
    assert decision.status == "APPROVED"
    assert decision.quorum_met is True

def test_duplicate_vote_rejected():
    _, repo = repository()
    repo.cast_vote(
        request_id="r1",
        voter="a",
        group="admin",
        approve=True,
        note="ok",
        now=10,
    )
    with pytest.raises(DuplicateVote):
        repo.cast_vote(
            request_id="r1",
            voter="a",
            group="security",
            approve=True,
            note="again",
            now=11,
        )

def test_any_rejection_rejects_request():
    _, repo = repository()
    repo.cast_vote(
        request_id="r1",
        voter="a",
        group="admin",
        approve=False,
        note="reject",
        now=10,
    )
    assert repo.decision("r1").status == "REJECTED"
