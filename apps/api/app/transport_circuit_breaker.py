from __future__ import annotations
from dataclasses import dataclass
import json
import time

@dataclass(frozen=True)
class CircuitBreakerState:
    name: str
    state: str
    failures: int
    opened_at: int | None
    next_probe_at: int | None
    last_error: str | None
    updated_at: int

class CircuitOpen(RuntimeError):
    pass

class RedisCircuitBreaker:
    def __init__(
        self,
        client,
        *,
        name: str,
        prefix: str = "aslan:circuit-breaker",
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        ttl_seconds: int = 86400,
    ):
        if failure_threshold <= 0:
            raise ValueError("failure_threshold pozitif olmalıdır")
        if recovery_timeout_seconds <= 0 or ttl_seconds <= 0:
            raise ValueError("Circuit breaker süreleri pozitif olmalıdır")
        self.client = client
        self.name = name
        self.prefix = prefix
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.ttl_seconds = ttl_seconds

    def before_call(
        self,
        *,
        now: int | None = None,
    ) -> CircuitBreakerState:
        current = int(now if now is not None else time.time())
        state = self.get()

        if state.state == "OPEN":
            if (
                state.next_probe_at is not None
                and current >= state.next_probe_at
            ):
                half_open = CircuitBreakerState(
                    name=self.name,
                    state="HALF_OPEN",
                    failures=state.failures,
                    opened_at=state.opened_at,
                    next_probe_at=None,
                    last_error=state.last_error,
                    updated_at=current,
                )
                self._save(half_open)
                return half_open
            raise CircuitOpen(
                f"Transport circuit açık: {self.name}"
            )

        return state

    def record_success(
        self,
        *,
        now: int | None = None,
    ) -> CircuitBreakerState:
        current = int(now if now is not None else time.time())
        state = CircuitBreakerState(
            name=self.name,
            state="CLOSED",
            failures=0,
            opened_at=None,
            next_probe_at=None,
            last_error=None,
            updated_at=current,
        )
        self._save(state)
        return state

    def record_failure(
        self,
        error: str,
        *,
        now: int | None = None,
    ) -> CircuitBreakerState:
        current = int(now if now is not None else time.time())
        previous = self.get()
        failures = previous.failures + 1

        if (
            previous.state == "HALF_OPEN"
            or failures >= self.failure_threshold
        ):
            state = CircuitBreakerState(
                name=self.name,
                state="OPEN",
                failures=failures,
                opened_at=current,
                next_probe_at=current + self.recovery_timeout_seconds,
                last_error=error[:1000],
                updated_at=current,
            )
        else:
            state = CircuitBreakerState(
                name=self.name,
                state="CLOSED",
                failures=failures,
                opened_at=None,
                next_probe_at=None,
                last_error=error[:1000],
                updated_at=current,
            )

        self._save(state)
        return state

    def get(self) -> CircuitBreakerState:
        payload = self.client.get(self._key())
        if payload is None:
            return CircuitBreakerState(
                name=self.name,
                state="CLOSED",
                failures=0,
                opened_at=None,
                next_probe_at=None,
                last_error=None,
                updated_at=0,
            )
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return CircuitBreakerState(**json.loads(payload))

    def reset(self) -> CircuitBreakerState:
        state = CircuitBreakerState(
            name=self.name,
            state="CLOSED",
            failures=0,
            opened_at=None,
            next_probe_at=None,
            last_error=None,
            updated_at=int(time.time()),
        )
        self._save(state)
        return state

    def _save(self, state: CircuitBreakerState) -> None:
        self.client.setex(
            self._key(),
            self.ttl_seconds,
            json.dumps(
                state.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

    def _key(self) -> str:
        return f"{self.prefix}:{self.name}"
