from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SmokeCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class SmokeReport:
    passed: bool
    checks: tuple[SmokeCheck, ...]


class SmokeTestRunner:
    def run(self, probes: dict[str, Callable[[], bool]]) -> SmokeReport:
        checks = []
        for name, probe in probes.items():
            try:
                ok = bool(probe())
                detail = "ok" if ok else "failed"
            except Exception as exc:
                ok = False
                detail = str(exc)
            checks.append(SmokeCheck(name, ok, detail))
        return SmokeReport(
            passed=all(check.passed for check in checks),
            checks=tuple(checks),
        )
