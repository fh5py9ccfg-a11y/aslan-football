from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PlatformReadiness:
    provider_configured: bool
    event_store_ready: bool
    decision_engine_ready: bool
    monitoring_ready: bool
    safe_mode: bool
    production_ready: bool
    blockers: tuple[str, ...]

@dataclass(frozen=True)
class LivePlatformResult:
    fixture_id: str
    accepted: bool
    event_applied: bool
    decision_outcome: str | None
    decision_confidence: float | None
    risk_score: float | None
    safe_mode: bool
    blockers: tuple[str, ...]
