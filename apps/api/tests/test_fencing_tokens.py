import pytest
from apps.api.app.distributed_lease import (
    RedisLease,
    StaleFencingToken,
)
from apps.api.app.fenced_redis import FencedRedisMutator

class FakeRedis:
    def __init__(self):
        self.values = {}
        self.ttls = {}
        self.sets = {"index": {"orphan"}}
        self.counter = 0

    def eval(self, script, number_of_keys, *args):
        if "INCR" in script:
            lease_key, counter_key, owner, ttl = args
            if lease_key in self.values:
                return [0, 0]
            self.counter += 1
            self.values[lease_key] = f"{owner}:{self.counter}"
            self.ttls[lease_key] = int(ttl)
            return [1, self.counter]

        if "SREM" in script:
            fence_key, index_key, token, session_id = args
            current = int(self.values.get(fence_key, 0))
            if int(token) < current:
                return [-1, current]
            self.values[fence_key] = int(token)
            removed = int(session_id in self.sets[index_key])
            self.sets[index_key].discard(session_id)
            return [removed, int(token)]

        key = args[0]
        owner = args[1]
        token = args[2] if len(args) > 2 else ""
        expected = f"{owner}:{token}"
        if self.values.get(key) != expected:
            return 0
        if "DEL" in script:
            self.values.pop(key, None)
            return 1
        return 1

    def get(self, key):
        return self.values.get(key)

    def ttl(self, key):
        return self.ttls.get(key, -2)

def test_stale_fencing_token_is_rejected():
    redis = FakeRedis()
    first = RedisLease(redis, key="lease", owner_id="a")
    second = RedisLease(redis, key="lease", owner_id="b")

    assert first.acquire()
    assert first.fencing_token == 1
    assert first.release()
    assert second.acquire()
    assert second.fencing_token == 2

    fresh = FencedRedisMutator(
        redis,
        fencing_token=2,
        fence_key="fence",
    )
    stale = FencedRedisMutator(
        redis,
        fencing_token=1,
        fence_key="fence",
    )

    assert fresh.remove_orphan("index", "orphan") == 1
    redis.sets["index"].add("orphan")

    with pytest.raises(StaleFencingToken):
        stale.remove_orphan("index", "orphan")
