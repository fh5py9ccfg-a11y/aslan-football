from __future__ import annotations
from collections import defaultdict, deque
from threading import Lock
import time

from fastapi import HTTPException, Request, status

class SlidingWindowRateLimiter:
    def __init__(self, *, limit: int, window_seconds: int):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("Rate limit değerleri pozitif olmalıdır")
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, now: float | None = None) -> None:
        current = now if now is not None else time.time()
        cutoff = current - self.window_seconds

        with self._lock:
            bucket = self._requests[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit aşıldı",
                )
            bucket.append(current)

rate_limiter = SlidingWindowRateLimiter(
    limit=120,
    window_seconds=60,
)

async def rate_limit_middleware(request: Request, call_next):
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = (
        forwarded.split(",")[0].strip()
        if forwarded
        else (request.client.host if request.client else "unknown")
    )
    rate_limiter.check(f"{client_ip}:{request.url.path}")
    return await call_next(request)
