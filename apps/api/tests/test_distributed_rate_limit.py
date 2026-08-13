from app.distributed_rate_limit import (
    RedisFixedWindowRateLimiter,
)

class FakeRedis:
    def __init__(self):
        self.values = {}
        self.expirations = {}

    def incr(self, key):
        self.values[key] = (
            self.values.get(key, 0) + 1
        )
        return self.values[key]

    def expire(self, key, seconds):
        self.expirations[key] = seconds
        return True

def test_redis_rate_limiter():
    redis = FakeRedis()
    limiter = RedisFixedWindowRateLimiter(
        redis,
        limit=2,
        window_seconds=60,
    )
    first = limiter.check(
        "client",
        now=120,
    )
    second = limiter.check(
        "client",
        now=121,
    )
    third = limiter.check(
        "client",
        now=122,
    )
    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.remaining == 0
    assert redis.expirations
