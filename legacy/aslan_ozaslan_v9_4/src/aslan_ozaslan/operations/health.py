from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class HealthCheck:
    name: str
    healthy: bool
    critical: bool
    message: str


@dataclass(frozen=True)
class HealthReport:
    healthy: bool
    degraded: bool
    checks: tuple[HealthCheck, ...]


class HealthMonitor:
    def run(self, probes: dict[str, tuple[Callable[[], bool], bool]]) -> HealthReport:
        checks = []
        for name, (probe, critical) in probes.items():
            try:
                passed = bool(probe())
                message = "ok" if passed else "failed"
            except Exception as exc:
                passed = False
                message = str(exc)
            checks.append(HealthCheck(name, passed, critical, message))

        healthy = all(check.healthy or not check.critical for check in checks)
        degraded = any(not check.healthy for check in checks)
        return HealthReport(healthy, degraded, tuple(checks))
