from __future__ import annotations

from .agents import TacticalAgent, PerformanceAgent, RiskAgent
from .consensus import MultiAgentTacticalConsensus
from .safety_gate import TacticalRecommendationSafetyGate

class FootballIntelligenceService:
    def __init__(
        self,
        *,
        agents=None,
        consensus=None,
        safety_gate=None,
    ):
        self.agents = agents or (
            TacticalAgent(),
            PerformanceAgent(),
            RiskAgent(),
        )
        self.consensus = consensus or MultiAgentTacticalConsensus()
        self.safety_gate = (
            safety_gate or TacticalRecommendationSafetyGate()
        )

    def recommend(self, context, *, safe_mode: bool = False):
        opinions = tuple(
            agent.evaluate(context)
            for agent in self.agents
        )
        recommendation = self.consensus.combine(opinions)
        approved = self.safety_gate.evaluate(
            recommendation,
            reliability_score=context.reliability_score,
            safe_mode=safe_mode,
        )
        return opinions, approved
