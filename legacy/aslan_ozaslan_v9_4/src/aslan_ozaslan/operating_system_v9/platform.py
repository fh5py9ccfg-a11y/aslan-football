from __future__ import annotations

class FootballOperatingSystem:
    def __init__(
        self,
        *,
        registry,
        orchestrator,
        audit_repository,
    ):
        self.registry = registry
        self.orchestrator = orchestrator
        self.audit_repository = audit_repository

    def decide(
        self,
        *,
        subject_id: str,
        context,
        safe_mode: bool = False,
    ):
        expert_decisions = self.registry.evaluate_all(context)
        decision = self.orchestrator.combine(
            subject_id=subject_id,
            decisions=expert_decisions,
            safe_mode=safe_mode,
        )
        self.audit_repository.append(
            decision,
            expert_decisions,
        )
        return decision, expert_decisions
