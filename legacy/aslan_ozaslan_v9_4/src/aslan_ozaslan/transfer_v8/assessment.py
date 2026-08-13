from __future__ import annotations

from .domain import TransferPlayerProfile, TransferAssessment
from .age_curve import AgeCurveModel
from .injury import InjuryRiskModel
from .economics import TransferEconomicsModel

class TransferIntelligenceService:
    def __init__(
        self,
        *,
        age_curve=None,
        injury_model=None,
        economics=None,
    ):
        self.age_curve = age_curve or AgeCurveModel()
        self.injury_model = injury_model or InjuryRiskModel()
        self.economics = economics or TransferEconomicsModel()

    def assess(
        self,
        profile: TransferPlayerProfile,
    ) -> TransferAssessment:
        profile.validate()

        performance_score = max(
            0.0,
            min(
                profile.current_value_score / 10.0
                + profile.form_trend * 0.05,
                1.0,
            ),
        )
        age_curve_score = self.age_curve.score(
            age=profile.age,
            position=profile.position,
        )
        injury = self.injury_model.evaluate(
            injury_days_last_365=profile.injury_days_last_365,
            minutes_last_365=profile.minutes_last_365,
        )
        economics = self.economics.evaluate(
            value_score=max(profile.current_value_score, 0.01),
            annual_salary=profile.annual_salary,
            estimated_fee=profile.estimated_fee,
        )
        leverage = self.economics.contract_leverage(
            contract_months_remaining=profile.contract_months_remaining,
        )
        league_adjustment = max(
            0.0,
            min(profile.league_strength, 1.0),
        )

        overall = (
            performance_score * 0.30
            + age_curve_score * 0.18
            + (1.0 - injury.risk_score) * 0.18
            + economics.score * 0.16
            + leverage * 0.08
            + league_adjustment * 0.10
        )

        warnings = []
        if injury.label == "HIGH":
            warnings.append("high_injury_risk")
        if profile.age >= 31:
            warnings.append("age_curve_decline")
        if economics.score < 0.35:
            warnings.append("poor_cost_efficiency")
        if profile.contract_months_remaining > 36:
            warnings.append("weak_contract_leverage")

        if overall >= 0.75 and not warnings:
            recommendation = "STRONG_BUY"
        elif overall >= 0.62:
            recommendation = "BUY_WITH_REVIEW"
        elif overall >= 0.48:
            recommendation = "WATCHLIST"
        else:
            recommendation = "PASS"

        return TransferAssessment(
            player_id=profile.player_id,
            performance_score=performance_score,
            age_curve_score=age_curve_score,
            injury_risk_score=injury.risk_score,
            cost_efficiency_score=economics.score,
            contract_leverage_score=leverage,
            league_adjustment_score=league_adjustment,
            overall_score=overall,
            recommendation=recommendation,
            warnings=tuple(warnings),
        )
