from __future__ import annotations
from abc import ABC, abstractmethod

from aslan_ozaslan.operating_system_v9 import ExpertDecision

class ExpertAdapter(ABC):
    name: str
    category: str

    @abstractmethod
    def evaluate(self, context) -> ExpertDecision:
        raise NotImplementedError

    def _decision(
        self,
        *,
        recommendation: str,
        confidence: float,
        risk: float,
        rationale: str,
    ) -> ExpertDecision:
        return ExpertDecision(
            expert=self.name,
            recommendation=recommendation,
            confidence=max(0.0, min(confidence, 1.0)),
            risk=max(0.0, min(risk, 1.0)),
            rationale=rationale,
            category=self.category,
        )
