from dataclasses import dataclass

@dataclass(frozen=True)
class PreflightCheck:
    name: str
    passed: bool
    critical: bool
    message: str

@dataclass(frozen=True)
class PreflightReport:
    ready: bool
    checks: tuple[PreflightCheck, ...]

class PreflightRunner:
    def run(self, checks):
        if not checks:
            raise ValueError("En az bir kontrol gereklidir")
        return PreflightReport(
            ready=all(c.passed or not c.critical for c in checks),
            checks=tuple(checks),
        )
