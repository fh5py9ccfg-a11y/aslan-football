from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class FinalReleaseDecision:
    approved: bool
    version: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

class FinalV7ReleaseGate:
    def evaluate(
        self,
        *,
        test_count: int,
        minimum_test_count: int,
        smoke_report,
        environment_report,
        platform_readiness,
    ) -> FinalReleaseDecision:
        blockers = []
        warnings = []

        if test_count < minimum_test_count:
            blockers.append("insufficient_test_count")
        if not smoke_report.passed:
            blockers.append("smoke_test_failed")
        if not smoke_report.provider_verified:
            blockers.append("provider_not_verified")
        if not environment_report.ready:
            blockers.extend(environment_report.blockers)
        if not platform_readiness.production_ready:
            blockers.extend(platform_readiness.blockers)

        warnings.extend(environment_report.warnings)

        return FinalReleaseDecision(
            approved=not blockers,
            version="7.0-final" if not blockers else "7.0-rc2",
            blockers=tuple(dict.fromkeys(blockers)),
            warnings=tuple(dict.fromkeys(warnings)),
        )
