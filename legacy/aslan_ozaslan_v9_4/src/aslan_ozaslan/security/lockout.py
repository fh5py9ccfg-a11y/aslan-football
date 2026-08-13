from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

@dataclass
class AttemptState:
    failures: int = 0
    locked_until: datetime | None = None

class LoginAttemptGuard:
    def __init__(self, max_failures: int = 5, lock_minutes: int = 15):
        if max_failures <= 0 or lock_minutes <= 0:
            raise ValueError("Kilit parametreleri pozitif olmalıdır")
        self.max_failures = max_failures
        self.lock_minutes = lock_minutes
        self._states: dict[str, AttemptState] = {}

    def is_locked(self, key: str) -> bool:
        state = self._states.get(key)
        if state is None or state.locked_until is None:
            return False
        if datetime.now(timezone.utc) >= state.locked_until:
            self._states[key] = AttemptState()
            return False
        return True

    def record_failure(self, key: str) -> None:
        state = self._states.setdefault(key, AttemptState())
        state.failures += 1
        if state.failures >= self.max_failures:
            state.locked_until = datetime.now(timezone.utc) + timedelta(minutes=self.lock_minutes)

    def record_success(self, key: str) -> None:
        self._states[key] = AttemptState()
