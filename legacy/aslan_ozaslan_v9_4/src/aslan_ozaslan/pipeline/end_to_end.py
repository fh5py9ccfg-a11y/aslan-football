from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from aslan_ozaslan.explainability import ExplanationBuilder, ExplanationFactor, PredictionExplanation
from aslan_ozaslan.league_config import LeagueParameterRegistry
from aslan_ozaslan.market import MarketAnalyzer, OddsSnapshot
from aslan_ozaslan.models_core import ExpectedGoalsEstimator, PoissonScoreModel, TeamStrengthInput
from aslan_ozaslan.squad import PlayerAvailability, SquadImpactCalculator


@dataclass(frozen=True)
class AnalysisInput:
    fixture_id: str
    competition_id: str
    kickoff_at: datetime
    home_team_id: str
    away_team_id: str
    home_strength: TeamStrengthInput
    away_strength: TeamStrengthInput
    home_players: tuple[PlayerAvailability, ...]
    away_players: tuple[PlayerAvailability, ...]
    odds: OddsSnapshot | None
    data_quality_score: int
    stale_data: bool = False
    postponed: bool = False


@dataclass(frozen=True)
class AnalysisOutput:
    status: str
    fixture_id: str
    calculation_id: str
    model_version: str
    home_probability: float | None
    draw_probability: float | None
    away_probability: float | None
    home_expected_goals: float | None
    away_expected_goals: float | None
    data_confidence: int
    explanation: PredictionExplanation | None
    market_probabilities: tuple[float, float, float] | None
    warnings: tuple[str, ...]


class EndToEndAnalysisPipeline:
    MODEL_VERSION = "v1.9-e2e"

    def __init__(self, league_registry: LeagueParameterRegistry):
        self.league_registry = league_registry
        self.squad_calculator = SquadImpactCalculator()
        self.market_analyzer = MarketAnalyzer()
        self.explanation_builder = ExplanationBuilder()
        self.score_model = PoissonScoreModel(max_goals=8)

    def analyze(self, item: AnalysisInput) -> AnalysisOutput:
        calculation_id = str(uuid4())
        warnings: list[str] = []

        if item.home_team_id == item.away_team_id:
            raise ValueError("Ev ve deplasman takımı aynı olamaz")
        if item.data_quality_score < 0 or item.data_quality_score > 100:
            raise ValueError("data_quality_score 0 ile 100 arasında olmalıdır")
        if item.postponed:
            return self._blocked(item, calculation_id, "Maç ertelendi.", 0)
        if item.stale_data:
            return self._blocked(item, calculation_id, "Veri güncel değil.", 0)

        parameters = self.league_registry.get(item.competition_id)
        if item.data_quality_score < 60:
            return self._blocked(
                item,
                calculation_id,
                "Veri kalite eşiği sağlanmadı.",
                item.data_quality_score,
            )

        home_squad = self.squad_calculator.calculate(list(item.home_players))
        away_squad = self.squad_calculator.calculate(list(item.away_players))

        adjusted_home = TeamStrengthInput(
            attack_rating=item.home_strength.attack_rating * home_squad.attack_multiplier,
            defense_rating=item.home_strength.defense_rating * home_squad.defense_multiplier,
            recent_form_points=item.home_strength.recent_form_points,
            elo_rating=item.home_strength.elo_rating,
        )
        adjusted_away = TeamStrengthInput(
            attack_rating=item.away_strength.attack_rating * away_squad.attack_multiplier,
            defense_rating=item.away_strength.defense_rating * away_squad.defense_multiplier,
            recent_form_points=item.away_strength.recent_form_points,
            elo_rating=item.away_strength.elo_rating,
        )

        estimator = ExpectedGoalsEstimator(
            league_goal_average=parameters.league_goal_average,
            home_advantage_multiplier=parameters.home_advantage_multiplier,
        )
        home_xg, away_xg = estimator.estimate(adjusted_home, adjusted_away)
        distribution = self.score_model.predict(home_xg, away_xg)

        market_tuple = None
        factors = [
            ExplanationFactor(
                "Takım güç dengesi",
                "HOME" if distribution.home_win > distribution.away_win else "AWAY",
                min(abs(distribution.home_win - distribution.away_win) * 2.0, 1.0),
                "Elo, hücum, savunma ve form birleşimi",
            )
        ]

        if home_squad.unavailable_count:
            warnings.append(f"Ev sahibinde {home_squad.unavailable_count} önemli eksik var.")
            factors.append(
                ExplanationFactor(
                    "Ev sahibi kadro eksikleri",
                    "AWAY",
                    min(0.3 + home_squad.unavailable_count * 0.1, 1.0),
                    "Eksik oyuncular hücum/savunma çarpanını düşürdü",
                )
            )
        if away_squad.unavailable_count:
            warnings.append(f"Deplasmanda {away_squad.unavailable_count} önemli eksik var.")
            factors.append(
                ExplanationFactor(
                    "Deplasman kadro eksikleri",
                    "HOME",
                    min(0.3 + away_squad.unavailable_count * 0.1, 1.0),
                    "Eksik oyuncular hücum/savunma çarpanını düşürdü",
                )
            )

        uncertainty = home_squad.uncertainty_penalty + away_squad.uncertainty_penalty
        if uncertainty > 0:
            warnings.append("Kadroda kesinleşmemiş oyuncu durumları var.")

        if item.odds is not None:
            market = self.market_analyzer.implied_probabilities(item.odds)
            market_tuple = (market.home, market.draw, market.away)
            model_probs = (distribution.home_win, distribution.draw, distribution.away_win)
            market_gap = max(abs(a - b) for a, b in zip(model_probs, market_tuple))
            if market_gap > 0.18:
                warnings.append("Model ile piyasa arasında yüksek fark var.")
            factors.append(
                ExplanationFactor(
                    "Piyasa karşılaştırması",
                    "NEUTRAL",
                    min(market_gap * 2.0, 1.0),
                    "Marjdan arındırılmış piyasa olasılıklarıyla karşılaştırıldı",
                )
            )

        confidence = int(
            max(
                0,
                min(
                    100,
                    item.data_quality_score
                    - round(uncertainty * 100)
                    - (10 if market_tuple is None else 0),
                ),
            )
        )

        limitations = list(warnings)
        if item.odds is None:
            limitations.append("Piyasa oranı bulunmadı.")
        if confidence < 70:
            limitations.append("Veri güveni yüksek seviyede değil.")

        explanation = self.explanation_builder.build(
            probabilities=(distribution.home_win, distribution.draw, distribution.away_win),
            factors=factors,
            limitations=limitations,
        )

        return AnalysisOutput(
            status="OK",
            fixture_id=item.fixture_id,
            calculation_id=calculation_id,
            model_version=self.MODEL_VERSION,
            home_probability=distribution.home_win,
            draw_probability=distribution.draw,
            away_probability=distribution.away_win,
            home_expected_goals=distribution.home_expected_goals,
            away_expected_goals=distribution.away_expected_goals,
            data_confidence=confidence,
            explanation=explanation,
            market_probabilities=market_tuple,
            warnings=tuple(warnings),
        )

    def _blocked(
        self,
        item: AnalysisInput,
        calculation_id: str,
        reason: str,
        confidence: int,
    ) -> AnalysisOutput:
        return AnalysisOutput(
            status="BLOCKED",
            fixture_id=item.fixture_id,
            calculation_id=calculation_id,
            model_version=self.MODEL_VERSION,
            home_probability=None,
            draw_probability=None,
            away_probability=None,
            home_expected_goals=None,
            away_expected_goals=None,
            data_confidence=confidence,
            explanation=None,
            market_probabilities=None,
            warnings=(reason,),
        )
