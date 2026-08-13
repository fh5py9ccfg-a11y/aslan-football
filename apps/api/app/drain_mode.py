from __future__ import annotations
from dataclasses import dataclass
import time

@dataclass(frozen=True)
class DrainState:
    enabled: bool
    reason: str | None
    started_at: int | None
    active_requests: int

class DrainController:
    def __init__(self):
        self.enabled = False
        self.reason = None
        self.started_at = None
        self.active_requests = 0
    def enter(self, *, reason: str, now: int | None = None):
        self.enabled = True
        self.reason = reason[:500]
        self.started_at = int(now if now is not None else time.time())
        return self.snapshot()
    def exit(self):
        self.enabled = False
        self.reason = None
        self.started_at = None
        return self.snapshot()
    def begin_request(self):
        self.active_requests += 1
    def finish_request(self):
        self.active_requests = max(0, self.active_requests - 1)
    def snapshot(self):
        return DrainState(self.enabled, self.reason, self.started_at, self.active_requests)

async def drain_middleware(request, call_next):
    controller = request.app.state.drain_controller
    exempt = {'/health', '/ready', '/live'}
    if controller.enabled and request.url.path not in exempt and not request.url.path.startswith('/admin/upgrade'):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={'detail': 'Instance drain modunda', 'retryable': True}, headers={'Retry-After': '5'})
    controller.begin_request()
    try:
        return await call_next(request)
    finally:
        controller.finish_request()
