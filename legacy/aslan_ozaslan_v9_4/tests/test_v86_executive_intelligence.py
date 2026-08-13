import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.executive_v8 import (
    ClubExecutiveSnapshot,
    SeasonObjective,
    SeasonObjectiveTracker,
    ExecutiveFinancialAnalyzer,
    MultiClubBenchmarkEngine,
    StrategicRiskEvaluator,
    ExecutiveIntelligenceService,
    ExecutiveDashboardService,
)
from aslan_ozaslan.admin.executive_intelligence_page import (
    render_executive_intelligence_page,
)

class ExecutiveIntelligenceTests(unittest.TestCase):
    def snapshot(self, club_id="club-a", sporting=0.76, financial=0.72):
        return ClubExecutiveSnapshot(
            club_id=club_id,
            sporting_score=sporting,
            financial_score=financial,
            squad_score=0.73,
            academy_score=0.66,
            transfer_score=0.70,
            risk_score=0.28,
            revenue=120_000_000,
            wage_cost=68_000_000,
            transfer_balance=8_000_000,
            average_squad_age=26.8,
        )

    def objectives(self):
        return (
            SeasonObjective("league_points", 75, 60, 0.50, True),
            SeasonObjective("wage_ratio", 0.60, 0.57, 0.25, False),
            SeasonObjective("academy_minutes", 3500, 2900, 0.25, True),
        )

    def test_objectives_financials_and_risk(self):
        tracker = SeasonObjectiveTracker()
        reports = tracker.evaluate(self.objectives())
        aggregate = tracker.aggregate(reports, self.objectives())
        self.assertTrue(0 < aggregate <= 1)

        financial = ExecutiveFinancialAnalyzer().evaluate(
            revenue=120_000_000,
            wage_cost=68_000_000,
            transfer_balance=8_000_000,
            cash_reserve=25_000_000,
            annual_commitments=30_000_000,
        )
        self.assertIn(financial.status, {"STABLE", "WATCH"})

        risk = StrategicRiskEvaluator().evaluate(
            squad_age=26.8,
            contract_risk=0.20,
            wage_ratio=financial.wage_to_revenue_ratio,
            academy_score=0.66,
            sporting_volatility=0.22,
        )
        self.assertEqual(risk.level, "CONTROLLED")

    def test_multi_club_benchmark(self):
        snapshots = [
            self.snapshot("club-a", 0.76, 0.72),
            self.snapshot("club-b", 0.68, 0.82),
            self.snapshot("club-c", 0.80, 0.60),
        ]
        results = MultiClubBenchmarkEngine().compare(snapshots)
        self.assertEqual(len(results), 3)
        self.assertEqual(
            sorted(item.overall_rank for item in results),
            [1, 2, 3],
        )

    def test_full_executive_report_dashboard_and_page(self):
        service = ExecutiveIntelligenceService()
        report = service.evaluate(
            snapshot=self.snapshot(),
            objectives=self.objectives(),
            cash_reserve=25_000_000,
            annual_commitments=30_000_000,
            contract_risk=0.20,
            sporting_volatility=0.22,
        )
        self.assertIn(report.status, {"HEALTHY", "WATCH"})
        self.assertTrue(report.priority_actions)

        dashboard = ExecutiveDashboardService().build(report)
        self.assertEqual(dashboard.club_id, "club-a")
        self.assertEqual(
            dashboard.action_count,
            len(report.priority_actions),
        )

        benchmarks = MultiClubBenchmarkEngine().compare([
            self.snapshot("club-a", 0.76, 0.72),
            self.snapshot("club-b", 0.68, 0.82),
        ])
        page = render_executive_intelligence_page(
            report,
            benchmarks,
        )
        self.assertIn("Executive Intelligence Center", page)
        self.assertIn("Öncelikli aksiyonlar", page)
        self.assertIn("Kulüp karşılaştırması", page)

if __name__ == "__main__":
    unittest.main()
