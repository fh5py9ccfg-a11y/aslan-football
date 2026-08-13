from __future__ import annotations

from .domain import OpponentPreparationReport
from .weakness import OpponentWeaknessAnalyzer
from .matchups import PlayerMatchupEngine
from .plans import MatchPlanGenerator
from .simulation import OpponentScenarioSimulator
from .briefing import MatchBriefingBuilder

class OpponentIntelligenceService:
    def __init__(
        self,
        *,
        weakness_analyzer=None,
        matchup_engine=None,
        plan_generator=None,
        simulator=None,
        briefing_builder=None,
    ):
        self.weakness_analyzer = (
            weakness_analyzer or OpponentWeaknessAnalyzer()
        )
        self.matchup_engine = matchup_engine or PlayerMatchupEngine()
        self.plan_generator = plan_generator or MatchPlanGenerator()
        self.simulator = simulator or OpponentScenarioSimulator()
        self.briefing_builder = briefing_builder or MatchBriefingBuilder()

    def prepare(
        self,
        *,
        opponent_dna,
        matchups,
        attack_strength: float,
        defense_strength: float,
        iterations: int = 5000,
        seed: int = 1,
    ) -> OpponentPreparationReport:
        weakness = self.weakness_analyzer.analyze(opponent_dna)

        critical = []
        for matchup in matchups:
            assessment = self.matchup_engine.evaluate(matchup)
            if assessment.label != "BALANCED":
                critical.append(
                    f"{matchup.our_player_id} vs "
                    f"{matchup.opponent_player_id}: "
                    f"{assessment.label}"
                )

        plans = self.plan_generator.generate(weakness)
        simulation = self.simulator.simulate(
            attack_strength=attack_strength,
            defense_strength=defense_strength,
            opponent_transition_threat=opponent_dna.transition_speed,
            opponent_set_piece_threat=opponent_dna.set_piece_threat,
            iterations=iterations,
            seed=seed,
        )
        briefing = self.briefing_builder.build(
            opponent_id=opponent_dna.team_id,
            weakness=weakness,
            matchups=critical,
            plans=plans,
            simulation=simulation,
        )

        return OpponentPreparationReport(
            opponent_id=opponent_dna.team_id,
            weakness_map=weakness,
            critical_matchups=tuple(critical),
            plans=plans,
            recommended_plan=plans[0].name,
            briefing=briefing,
        )
