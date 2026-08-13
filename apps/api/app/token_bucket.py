from dataclasses import dataclass
import time
from starlette.responses import JSONResponse

@dataclass(frozen=True)
class TokenBucketDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: int

class RedisTokenBucketRateLimiter:
    LUA_SCRIPT = '''
    local key = KEYS[1]
    local capacity = tonumber(ARGV[1])
    local refill_rate = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])
    local requested = tonumber(ARGV[4])
    local ttl = tonumber(ARGV[5])

    local values = redis.call('HMGET', key, 'tokens', 'updated_at')
    local tokens = tonumber(values[1])
    local updated_at = tonumber(values[2])

    if tokens == nil then
        tokens = capacity
        updated_at = now
    end

    local elapsed = math.max(0, now - updated_at)
    tokens = math.min(capacity, tokens + elapsed * refill_rate)

    local allowed = 0
    if tokens >= requested then
        tokens = tokens - requested
        allowed = 1
    end

    redis.call('HMSET', key, 'tokens', tokens, 'updated_at', now)
    redis.call('EXPIRE', key, ttl)

    return {allowed, math.floor(tokens)}
    '''

    def __init__(
        self,
        client,
        *,
        capacity=120,
        refill_per_second=2.0,
        prefix="aslan:tokenbucket",
    ):
        if capacity <= 0 or refill_per_second <= 0:
            raise ValueError(
                "Token bucket değerleri pozitif olmalıdır"
            )
        self.client = client
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self.prefix = prefix

    def check(
        self,
        key,
        *,
        now=None,
        requested=1,
    ):
        current = float(
            now if now is not None else time.time()
        )
        ttl = max(
            1,
            int(
                self.capacity
                / self.refill_per_second
                * 2
            ),
        )

        allowed, remaining = self.client.eval(
            self.LUA_SCRIPT,
            1,
            f"{self.prefix}:{key}",
            self.capacity,
            self.refill_per_second,
            current,
            requested,
            ttl,
        )
        retry_after = (
            0
            if int(allowed) == 1
            else max(
                1,
                int(
                    requested
                    / self.refill_per_second
                ),
            )
        )
        return TokenBucketDecision(
            allowed=int(allowed) == 1,
            remaining=int(remaining),
            retry_after_seconds=retry_after,
        )

def build_token_bucket_limiter():
    import os
    from redis import Redis

    client = Redis.from_url(
        os.getenv(
            "REDIS_URL",
            "redis://redis:6379/0",
        ),
        decode_responses=True,
    )
    return RedisTokenBucketRateLimiter(
        client,
        capacity=int(
            os.getenv(
                "RATE_LIMIT_CAPACITY",
                "120",
            )
        ),
        refill_per_second=float(
            os.getenv(
                "RATE_LIMIT_REFILL_PER_SECOND",
                "2",
            )
        ),
    )

async def token_bucket_middleware(
    request,
    call_next,
):
    limiter = request.app.state.rate_limiter
    forwarded = request.headers.get(
        "X-Forwarded-For"
    )
    client_ip = (
        forwarded.split(",")[0].strip()
        if forwarded
        else (
            request.client.host
            if request.client
            else "unknown"
        )
    )
    decision = limiter.check(
        f"{client_ip}:{request.url.path}"
    )

    if not decision.allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit aşıldı"
            },
            headers={
                "Retry-After": str(
                    decision.retry_after_seconds
                ),
                "X-RateLimit-Remaining": "0",
            },
        )

    response = await call_next(request)
    response.headers[
        "X-RateLimit-Remaining"
    ] = str(decision.remaining)
    return response
