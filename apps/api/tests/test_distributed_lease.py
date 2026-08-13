from apps.api.app.distributed_lease import (
    RedisLease,
)

class FakeRedis:
    def __init__(self):
        self.values = {}
        self.ttls = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        self.ttls[key] = ex
        return True

    def get(self, key):
        return self.values.get(key)

    def ttl(self, key):
        return self.ttls.get(key, -2)

    def eval(self, script, number_of_keys, key, *args):
        owner = args[0]
        if self.values.get(key) != owner:
            return 0
        if "DEL" in script:
            self.values.pop(key, None)
            self.ttls.pop(key, None)
            return 1
        self.ttls[key] = int(args[1])
        return 1

def test_lease_acquire_renew_release():
    redis = FakeRedis()
    first = RedisLease(
        redis,
        key="lease",
        ttl_seconds=30,
        owner_id="owner-1",
    )
    second = RedisLease(
        redis,
        key="lease",
        ttl_seconds=30,
        owner_id="owner-2",
    )

    assert first.acquire() is True
    assert second.acquire() is False
    assert first.state().acquired is True
    assert first.renew() is True
    assert second.release() is False
    assert first.release() is True
    assert second.acquire() is True
