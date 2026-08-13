from __future__ import annotations
from dataclasses import dataclass

from .domain import ExplanationFactor, NormalizedFactor
from .contributions import ContributionNormalizer
from .consensus import ModelVote, ConsensusReport, EnsembleConsensusAnalyzer
from .reliability import (
    ReliabilityInput,
    ReliabilityReport,
    PredictionReliabilityEvaluator,
)
from .narrative import FootballNarrativeBuilder

@dataclass(frozen=True)
class ExplainablePredictionReport:
    outcome: str
    probability: float
    factors: tuple[NormalizedFactor, ...]
    consensus: ConsensusReport
    reliability: ReliabilityReport
    narrative: str

class ExplainablePredictionService:
    def build(
        self,
        *,
        outcome: str,
        probability: float,
        factors: list[ExplanationFactor],
        model_votes: list[ModelVote],
        calibration_error: float,
        sample_adequacy: float,
        data_freshness: float,
        simulation_stability: float,
    ) -> ExplainablePredictionReport:
        normalized = ContributionNormalizer().normalize(factors)
        consensus = EnsembleConsensusAnalyzer().analyze(model_votes)
        reliability = PredictionReliabilityEvaluator().evaluate(
            ReliabilityInput(
                calibration_error=calibration_error,
                sample_adequacy=sample_adequacy,
                data_freshness=data_freshness,
                consensus=consensus,
                simulation_stability=simulation_stability,
            )
        )
        narrative = FootballNarrativeBuilder().build(
            outcome=outcome,
            probability=probability,
            factors=normalized,
            reliability_label=reliability.label,
        )

        return ExplainablePredictionReport(
            outcome=outcome,
            probability=probability,
            factors=normalized,
            consensus=consensus,
            reliability=reliability,
            narrative=narrative,
        )
