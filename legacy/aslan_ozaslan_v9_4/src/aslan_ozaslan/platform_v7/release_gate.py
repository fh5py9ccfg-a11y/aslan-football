from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ReleaseCandidateDecision:
    approved: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

class V7ReleaseGate:
    def evaluate(
        self,
        *,
        tests_passed: bool,
        readiness,
        minimum_test_count: int,
        observed_test_count: int,
        live_api_verified: bool,
    ) -> ReleaseCandidateDecision:
        blockers = []
        warnings = []

        if not tests_passed:
            blockers.append("test_suite_failed")
        if observed_test_count < minimum_test_count:
            blockers.append("insufficient_test_count")
        if not readiness.production_ready:
            blockers.extend(readiness.blockers)
        if not live_api_verified:
            warnings.append("live_api_not_yet_verified")

        return ReleaseCandidateDecision(
            approved=not blockers,
            blockers=tuple(dict.fromkeys(blockers)),
            warnings=tuple(warnings),
        )
