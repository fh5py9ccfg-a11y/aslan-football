from __future__ import annotations

from .domain import PlatformReadiness

class PlatformReadinessEvaluator:
    def evaluate(
        self,
        *,
        provider_configured: bool,
        event_store_ready: bool,
        decision_engine_ready: bool,
        monitoring_ready: bool,
        safe_mode: bool,
    ) -> PlatformReadiness:
        blockers = []

        if not provider_configured:
            blockers.append("provider_not_configured")
        if not event_store_ready:
            blockers.append("event_store_not_ready")
        if not decision_engine_ready:
            blockers.append("decision_engine_not_ready")
        if not monitoring_ready:
            blockers.append("monitoring_not_ready")
        if safe_mode:
            blockers.append("safe_mode_active")

        return PlatformReadiness(
            provider_configured=provider_configured,
            event_store_ready=event_store_ready,
            decision_engine_ready=decision_engine_ready,
            monitoring_ready=monitoring_ready,
            safe_mode=safe_mode,
            production_ready=not blockers,
            blockers=tuple(blockers),
        )
