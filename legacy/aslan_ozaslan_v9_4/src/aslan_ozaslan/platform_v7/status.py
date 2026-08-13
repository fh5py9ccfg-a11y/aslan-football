from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PlatformStatus:
    version: str
    production_ready: bool
    safe_mode: bool
    test_count: int
    active_fixture_count: int
    provider_connected: bool

class PlatformStatusService:
    def build(
        self,
        *,
        readiness,
        test_count: int,
        active_fixture_count: int,
    ) -> PlatformStatus:
        return PlatformStatus(
            version="7.0-rc1",
            production_ready=readiness.production_ready,
            safe_mode=readiness.safe_mode,
            test_count=test_count,
            active_fixture_count=active_fixture_count,
            provider_connected=readiness.provider_configured,
        )
