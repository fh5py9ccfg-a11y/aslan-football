from __future__ import annotations
from dataclasses import dataclass
import time

from .domain import DecisionContext, DecisionSnapshot
from .signal_engine import LiveSignalEngine
from .risk import RiskOpportunityEvaluator

@dataclass(frozen=True)
class DecisionRunReport:
    snapshot: DecisionSnapshot
    latency_ms: float
    degraded: bool

class RealTimeDecisionEngine:
    def __init__(
        self,
        *,
        latency_budget_ms: float = 50.0,
    ):
        if latency_budget_ms <= 0:
            raise ValueError("latency_budget_ms pozitif olmalıdır")
        self.latency_budget_ms = latency_budget_ms
        self.signal_engine = LiveSignalEngine()
        self.risk_evaluator = RiskOpportunityEvaluator()

    def evaluate(
        self,
        context: DecisionContext,
    ) -> DecisionRunReport:
        started = time.perf_counter()
        context.validate()

        signals = self.signal_engine.generate(context)
        assessment = self.risk_evaluator.evaluate(context, signals)

        probabilities = {
            "HOME": context.home_probability,
            "DRAW": context.draw_probability,
            "AWAY": context.away_probability,
        }
        recommended = max(probabilities, key=probabilities.get)
        confidence = probabilities[recommended] * context.reliability_score

        snapshot = DecisionSnapshot(
            fixture_id=context.fixture_id,
            minute=context.minute,
            recommended_outcome=recommended,
            confidence=confidence,
            risk_score=assessment.risk_score,
            opportunity_score=assessment.opportunity_score,
            signals=signals,
        )

        latency = (time.perf_counter() - started) * 1000.0
        return DecisionRunReport(
            snapshot=snapshot,
            latency_ms=latency,
            degraded=latency > self.latency_budget_ms,
        )
