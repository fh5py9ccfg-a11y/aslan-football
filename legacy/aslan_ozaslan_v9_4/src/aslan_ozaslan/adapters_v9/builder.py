from __future__ import annotations

from aslan_ozaslan.operating_system_v9 import (
    ExpertRegistry,
    FootballDecisionOrchestrator,
    FootballOperatingSystem,
)

class FootballOperatingSystemBuilder:
    def __init__(self):
        self.registry = ExpertRegistry()
        self.weights = {}
        self.minimum_consensus = 0.55
        self.maximum_risk = 0.70

    def add_adapter(self, adapter, *, weight: float = 1.0):
        if weight <= 0:
            raise ValueError("weight pozitif olmalıdır")
        self.registry.register(adapter.name, adapter)
        self.weights[adapter.name] = weight
        return self

    def with_policy(
        self,
        *,
        minimum_consensus: float,
        maximum_risk: float,
    ):
        self.minimum_consensus = minimum_consensus
        self.maximum_risk = maximum_risk
        return self

    def build(self, *, audit_repository):
        orchestrator = FootballDecisionOrchestrator(
            expert_weights=self.weights,
            minimum_consensus=self.minimum_consensus,
            maximum_risk=self.maximum_risk,
        )
        return FootballOperatingSystem(
            registry=self.registry,
            orchestrator=orchestrator,
            audit_repository=audit_repository,
        )
