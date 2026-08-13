import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.opponent_v8 import (
    OpponentDNA,
    OpponentWeaknessAnalyzer,
    PlayerMatchup,
    PlayerMatchupEngine,
    MatchPlanGenerator,
    OpponentScenarioSimulator,
    OpponentIntelligenceService,
)
from aslan_ozaslan.admin.opponent_intelligence_page import (
    render_opponent_intelligence_page,
)

class OpponentIntelligenceTests(unittest.TestCase):
    def dna(self):
        return OpponentDNA(
            team_id="opp-1",
            possession=0.58,
            directness=0.42,
            pressing=0.76,
            defensive_line=0.80,
            transition_speed=0.72,
            left_attack_share=0.30,
            right_attack_share=0.42,
            central_attack_share=0.28,
            set_piece_threat=0.66,
            build_up_risk=0.68,
        )

    def matchups(self):
        return [
            PlayerMatchup(
                "our-lw","opp-rb","LEFT",
                0.82,0.66,0.30,0.05,0.20,
            ),
            PlayerMatchup(
                "our-st","opp-cb","CENTRAL",
                0.74,0.78,-0.05,-0.10,0.02,
            ),
        ]

    def test_weakness_and_matchups(self):
        weakness = OpponentWeaknessAnalyzer().analyze(self.dna())
        self.assertGreater(weakness.transition_defense, 0.5)

        assessment = PlayerMatchupEngine().evaluate(
            self.matchups()[0]
        )
        self.assertEqual(assessment.label, "OUR_ADVANTAGE")

    def test_plans_and_simulation(self):
        weakness = OpponentWeaknessAnalyzer().analyze(self.dna())
        plans = MatchPlanGenerator().generate(weakness)
        self.assertEqual(len(plans), 3)
        self.assertEqual(plans[0].name, "PLAN_A")

        simulation = OpponentScenarioSimulator().simulate(
            attack_strength=0.74,
            defense_strength=0.70,
            opponent_transition_threat=0.72,
            opponent_set_piece_threat=0.66,
            iterations=1000,
            seed=5,
        )
        self.assertGreater(simulation.expected_goals_for, 0)
        self.assertTrue(
            0 <= simulation.first_goal_probability <= 1
        )

    def test_full_report_and_page(self):
        report = OpponentIntelligenceService().prepare(
            opponent_dna=self.dna(),
            matchups=self.matchups(),
            attack_strength=0.74,
            defense_strength=0.70,
            iterations=1000,
            seed=5,
        )
        self.assertEqual(report.recommended_plan, "PLAN_A")
        self.assertTrue(report.briefing)
        self.assertGreaterEqual(len(report.plans), 3)

        page = render_opponent_intelligence_page(report)
        self.assertIn(
            "Opponent Intelligence & Match Preparation",
            page,
        )
        self.assertIn("Kritik eşleşmeler", page)
        self.assertIn("Maç planları", page)

if __name__ == "__main__":
    unittest.main()
