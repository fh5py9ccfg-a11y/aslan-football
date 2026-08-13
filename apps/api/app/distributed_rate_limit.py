from dataclasses import dataclass
import time
from starlette.responses import JSONResponse

@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    reset_after_seconds: int

class RedisFixedWindowRateLimiter:
    def __init__(
        self,
        client,
        *,
        limit=120,
        window_seconds=60,
        prefix="aslan:ratelimit",
    ):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("Rate limit değerleri pozitif olmalıdır")
        self.client = client
        self.limit = limit
        self.window_seconds = window_seconds
        self.prefix = prefix

    def check(self, key, *, now=None):
        current = int(now if now is not None else time.time())
        window = current // self.window_seconds
        redis_key = f"{self.prefix}:{key}:{window}"
        value = int(self.client.incr(redis_key))
        if value == 1:
            self.client.expire(redis_key, self.window_seconds + 1)
        remaining = max(0, self.limit - value)
        reset_after = self.window_seconds - (
            current % self.window_seconds
        )
        return RateLimitDecision(
            value <= self.limit,
            remaining,
            reset_after,
        )

def build_redis_rate_limiter():
    import os
    from redis import Redis

    client = Redis.from_url(
        os.getenv("REDIS_URL", "redis://redis:6379/0"),
        decode_responses=True,
    )
    return RedisFixedWindowRateLimiter(
        client,
        limit=int(os.getenv("RATE_LIMIT_REQUESTS", "120")),
        window_seconds=int(
            os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")
        ),
    )

async def distributed_rate_limit_middleware(
    request,
    call_next,
):
    limiter = request.app.state.rate_limiter
    forwarded = request.headers.get("X-Forwarded-For")
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
            content={"detail": "Rate limit aşıldı"},
            headers={
                "Retry-After": str(
                    decision.reset_after_seconds
                ),
                "X-RateLimit-Remaining": "0",
            },
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(
        decision.remaining
    )
    response.headers["X-RateLimit-Reset"] = str(
        decision.reset_after_seconds
    )
    return response
