from __future__ import annotations
from datetime import datetime, timezone

from aslan_ozaslan.event_sourcing_v6 import DomainEvent
from aslan_ozaslan.integration_v6 import ProviderFixtureSnapshot
from aslan_ozaslan.monitoring_v6 import DecisionQualitySample
from .domain import LivePlatformResult

class UnifiedLiveAnalyticsPipeline:
    def __init__(
        self,
        *,
        event_store,
        provider_event_orchestrator,
        decision_orchestrator,
        monitoring_window,
        readiness_evaluator,
    ):
        self.event_store = event_store
        self.provider_event_orchestrator = provider_event_orchestrator
        self.decision_orchestrator = decision_orchestrator
        self.monitoring_window = monitoring_window
        self.readiness_evaluator = readiness_evaluator

    def process(
        self,
        *,
        snapshot: ProviderFixtureSnapshot,
        provider_event,
        live_processor,
        reliability_score: float,
        provider_configured: bool,
        monitoring_ready: bool,
        safe_mode: bool,
    ) -> LivePlatformResult:
        readiness = self.readiness_evaluator.evaluate(
            provider_configured=provider_configured,
            event_store_ready=self.event_store is not None,
            decision_engine_ready=self.decision_orchestrator is not None,
            monitoring_ready=monitoring_ready,
            safe_mode=safe_mode,
        )

        if not readiness.production_ready:
            return LivePlatformResult(
                fixture_id=snapshot.fixture_id,
                accepted=False,
                event_applied=False,
                decision_outcome=None,
                decision_confidence=None,
                risk_score=None,
                safe_mode=safe_mode,
                blockers=readiness.blockers,
            )

        update = self.provider_event_orchestrator.process(
            snapshot=snapshot,
            record=provider_event,
        )

        if not update.accepted:
            return LivePlatformResult(
                fixture_id=snapshot.fixture_id,
                accepted=False,
                event_applied=False,
                decision_outcome=None,
                decision_confidence=None,
                risk_score=None,
                safe_mode=False,
                blockers=("provider_event_rejected",),
            )

        sequence = self.event_store.last_sequence(snapshot.fixture_id) + 1
        domain_event = DomainEvent(
            event_id=(
                f"{snapshot.fixture_id}:provider:"
                f"{provider_event.provider_event_id}:v{sequence}"
            ),
            fixture_id=snapshot.fixture_id,
            sequence=sequence,
            event_type=provider_event.event_type.upper(),
            occurred_at=datetime.now(timezone.utc).isoformat(),
            payload={
                "minute": provider_event.minute,
                "team_id": provider_event.team_id,
                "value": provider_event.value,
            },
            correlation_id=snapshot.fixture_id,
            causation_id=provider_event.provider_event_id,
            metadata={"source": "provider"},
        )
        event_applied = self.event_store.append(domain_event)

        momentum = live_processor.momentum_analyzer.analyze(
            events=live_processor.store.ordered(),
            home_team_id=live_processor.home_team_id,
            away_team_id=live_processor.away_team_id,
            current_minute=live_processor.state.minute,
        )

        decision_report = self.decision_orchestrator.on_live_state(
            fixture_id=snapshot.fixture_id,
            live_state=live_processor.state,
            momentum=momentum,
            reliability_score=reliability_score,
        )

        quality = DecisionQualitySample(
            fixture_id=snapshot.fixture_id,
            minute=decision_report.snapshot.minute,
            confidence=decision_report.snapshot.confidence,
            risk_score=decision_report.snapshot.risk_score,
            opportunity_score=decision_report.snapshot.opportunity_score,
            latency_ms=decision_report.latency_ms,
            degraded=decision_report.degraded,
        )
        self.monitoring_window.add(quality)

        return LivePlatformResult(
            fixture_id=snapshot.fixture_id,
            accepted=True,
            event_applied=event_applied,
            decision_outcome=decision_report.snapshot.recommended_outcome,
            decision_confidence=decision_report.snapshot.confidence,
            risk_score=decision_report.snapshot.risk_score,
            safe_mode=False,
            blockers=(),
        )
