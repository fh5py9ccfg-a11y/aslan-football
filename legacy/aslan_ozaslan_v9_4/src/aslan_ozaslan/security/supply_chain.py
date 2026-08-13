from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DependencyFinding:
    package: str
    severity: str
    fixed_version: str | None


@dataclass(frozen=True)
class SupplyChainReport:
    allowed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


class SupplyChainGate:
    BLOCKING_SEVERITIES = {"CRITICAL", "HIGH"}

    def evaluate(self, findings: list[DependencyFinding]) -> SupplyChainReport:
        blockers = []
        warnings = []

        for finding in findings:
            severity = finding.severity.upper()
            message = f"{finding.package}:{severity}"

            if severity in self.BLOCKING_SEVERITIES:
                blockers.append(message)
            elif severity in {"MEDIUM", "LOW"}:
                warnings.append(message)
            else:
                warnings.append(f"{finding.package}:UNKNOWN")

        return SupplyChainReport(
            allowed=not blockers,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
        )
