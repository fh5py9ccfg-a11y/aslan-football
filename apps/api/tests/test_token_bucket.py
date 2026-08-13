from app.token_bucket import (
    RedisTokenBucketRateLimiter,
)

class FakeRedis:
    def __init__(self):
        self.tokens = 2

    def eval(
        self,
        script,
        number_of_keys,
        key,
        capacity,
        refill_rate,
        now,
        requested,
        ttl,
    ):
        if self.tokens >= requested:
            self.tokens -= requested
            return [1, self.tokens]
        return [0, self.tokens]

def test_token_bucket_limiter():
    redis = FakeRedis()
    limiter = RedisTokenBucketRateLimiter(
        redis,
        capacity=2,
        refill_per_second=1,
    )

    first = limiter.check("client", now=100)
    second = limiter.check("client", now=100)
    third = limiter.check("client", now=100)

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.retry_after_seconds == 1
