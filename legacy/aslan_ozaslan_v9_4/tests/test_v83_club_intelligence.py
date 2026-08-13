import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.club_v8 import (
    ClubPlayerContract,
    SquadBalanceAnalyzer,
    ContractRiskAnalyzer,
    ClubBudget,
    ClubBudgetAnalyzer,
    TransferScenarioSimulator,
    ClubAIAdvisor,
)
from aslan_ozaslan.admin.club_intelligence_page import (
    render_club_intelligence_page,
)

class ClubIntelligenceTests(unittest.TestCase):
    def players(self):
        return [
            ClubPlayerContract("gk1","GK",28,0.78,2_000_000,10_000_000,24),
            ClubPlayerContract("gk2","GK",21,0.65,700_000,4_000_000,36),
            ClubPlayerContract("df1","DF",30,0.80,2_500_000,12_000_000,8),
            ClubPlayerContract("df2","DF",24,0.74,1_400_000,8_000_000,30),
            ClubPlayerContract("mf1","MF",26,0.84,3_000_000,18_000_000,18),
            ClubPlayerContract("mf2","MF",20,0.70,800_000,7_000_000,42,True),
            ClubPlayerContract("fw1","FW",29,0.86,4_000_000,20_000_000,10),
            ClubPlayerContract("fw2","FW",22,0.73,1_000_000,9_000_000,36),
        ]

    def test_squad_and_contract_analysis(self):
        report = SquadBalanceAnalyzer().analyze(self.players())
        self.assertEqual(report.squad_size, 8)
        self.assertGreater(report.depth_score, 0.9)

        risk = ContractRiskAnalyzer().evaluate(self.players()[2])
        self.assertEqual(risk.risk_level, "HIGH")

    def test_budget_and_scenario(self):
        budget = ClubBudgetAnalyzer().evaluate(
            ClubBudget(
                transfer_budget=25_000_000,
                salary_budget=20_000_000,
                current_salary=15_400_000,
            )
        )
        self.assertEqual(budget.status, "HEALTHY")

        incoming = ClubPlayerContract(
            "fw3","FW",21,0.78,1_800_000,12_000_000,48
        )
        scenario = TransferScenarioSimulator().simulate(
            current_players=self.players(),
            outgoing_player_ids=("fw1",),
            incoming_players=(incoming,),
            transfer_income=22_000_000,
            transfer_spend=12_000_000,
        )
        self.assertGreater(scenario.budget_delta, 0)
        self.assertLess(
            scenario.total_salary_after,
            scenario.total_salary_before,
        )

    def test_advisor_and_page(self):
        players = self.players()
        squad = SquadBalanceAnalyzer().analyze(players)
        budget = ClubBudgetAnalyzer().evaluate(
            ClubBudget(
                transfer_budget=15_000_000,
                salary_budget=16_000_000,
                current_salary=squad.total_salary,
            )
        )
        risks = tuple(
            ContractRiskAnalyzer().evaluate(player)
            for player in players
        )
        advice = ClubAIAdvisor().advise(
            squad_report=squad,
            budget_assessment=budget,
            contract_risks=risks,
        )
        self.assertTrue(advice)

        page = render_club_intelligence_page(
            squad,
            budget,
            advice,
        )
        self.assertIn("Club Intelligence & Squad Planning", page)
        self.assertIn("Club AI Advisor", page)
        self.assertIn("Sözleşme riski", page)

if __name__ == "__main__":
    unittest.main()
