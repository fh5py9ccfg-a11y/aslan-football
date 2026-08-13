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

    def smembers(self, key):
        return self.sets.get(key, set())

    def srem(self, key, value):
        self.sets.setdefault(key, set()).discard(value)

def test_compensation_lifecycle():
    repo = RedisCompensationRepository(
        Redis(),
        prefix="comp",
    )

    record = repo.create(
        request_id="r1",
        claim_id="c1",
        action="RECONCILE",
        reason="partial failure",
        now=1,
    )
    assert record.status == "PENDING"

    completed = repo.mark_completed(
        record,
        now=2,
    )
    assert completed.status == "COMPLETED"
    assert completed.attempts == 1
