from __future__ import annotations
from dataclasses import dataclass

from .domain import DecisionContext, DecisionSignal

@dataclass(frozen=True)
class RiskOpportunityAssessment:
    risk_score: float
    opportunity_score: float
    dominant_side: str

class RiskOpportunityEvaluator:
    def evaluate(
        self,
        context: DecisionContext,
        signals: tuple[DecisionSignal, ...],
    ) -> RiskOpportunityAssessment:
        context.validate()

        reliability_risk = 1.0 - context.reliability_score
        draw_uncertainty = context.draw_probability
        card_volatility = min(
            (context.home_red_cards + context.away_red_cards) * 0.25,
            1.0,
        )
        late_game_pressure = (
            max(0.0, (context.minute - 70) / 25.0)
            if context.home_goals != context.away_goals
            else 0.0
        )

        risk = min(
            reliability_risk * 0.35
            + draw_uncertainty * 0.25
            + card_volatility * 0.20
            + late_game_pressure * 0.20,
            1.0,
        )

        strongest_probability = max(
            context.home_probability,
            context.draw_probability,
            context.away_probability,
        )
        momentum_bonus = min(abs(context.momentum_edge) / 5.0, 1.0)
        signal_bonus = min(
            sum(signal.strength for signal in signals if signal.side != "NEUTRAL")
            / 4.0,
            1.0,
        )

        opportunity = min(
            strongest_probability * 0.55
            + context.reliability_score * 0.25
            + momentum_bonus * 0.10
            + signal_bonus * 0.10,
            1.0,
        )

        probabilities = {
            "HOME": context.home_probability,
            "DRAW": context.draw_probability,
            "AWAY": context.away_probability,
        }
        dominant = max(probabilities, key=probabilities.get)

        return RiskOpportunityAssessment(
            risk_score=risk,
            opportunity_score=opportunity,
            dominant_side=dominant,
        )
