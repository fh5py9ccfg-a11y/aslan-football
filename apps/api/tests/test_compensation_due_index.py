from apps.api.app.compensation import (
    RedisCompensationRepository,
)

class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def srem(self, key, value):
        self.sets.setdefault(key, set()).discard(value)

    def smembers(self, key):
        return self.sets.get(key, set())

def test_due_listing_and_requeue():
    repo = RedisCompensationRepository(
        Redis(),
        prefix="comp",
    )
    record = repo.create(
        request_id="r1",
        claim_id="c1",
        action="ACTION",
        reason="failure",
        now=100,
    )

    due = repo.list_due(
        now=100,
    )
    assert len(due) == 1

    retry = repo.schedule_retry(
        record,
        reason="again",
        next_attempt_at=200,
    )
    assert repo.list_due(now=150) == ()

    requeued = repo.requeue(
        retry,
        now=150,
    )
    assert requeued.status == "PENDING"
    assert len(repo.list_due(now=150)) == 1
