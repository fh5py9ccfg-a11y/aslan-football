import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.intelligence_v8 import (
    TacticalRecommendationContext,
    TacticalAgent,
    PerformanceAgent,
    RiskAgent,
    MultiAgentTacticalConsensus,
    TacticalRecommendationSafetyGate,
    FootballIntelligenceService,
    RecommendationHistoryRepository,
)
from aslan_ozaslan.admin.football_intelligence_page import (
    render_football_intelligence_page,
)

class FootballIntelligenceTests(unittest.TestCase):
    def context(self, reliability=0.88, fatigue=0.80):
        return TacticalRecommendationContext(
            fixture_id="f1",
            minute=82,
            goal_difference=-1,
            possession=0.48,
            pressing=0.72,
            defensive_line=0.68,
            width=0.60,
            tempo=0.75,
            momentum_edge=1.8,
            fatigue_level=fatigue,
            reliability_score=reliability,
        )

    def test_agents_generate_opinions(self):
        context = self.context()
        opinions = (
            TacticalAgent().evaluate(context),
            PerformanceAgent().evaluate(context),
            RiskAgent().evaluate(context),
        )
        self.assertEqual(len(opinions), 3)
        self.assertTrue(all(op.rationale for op in opinions))

    def test_consensus_and_safety_gate(self):
        context = self.context()
        opinions = (
            TacticalAgent().evaluate(context),
            PerformanceAgent().evaluate(context),
            RiskAgent().evaluate(context),
        )
        recommendation = MultiAgentTacticalConsensus().combine(opinions)
        gated = TacticalRecommendationSafetyGate(
            minimum_confidence=0.50,
            maximum_risk=0.80,
        ).evaluate(
            recommendation,
            reliability_score=context.reliability_score,
            safe_mode=False,
        )
        self.assertTrue(0 <= gated.confidence <= 1)
        self.assertTrue(0 <= gated.risk <= 1)

    def test_low_reliability_forces_manual_review(self):
        context = self.context(reliability=0.40, fatigue=0.20)
        opinions, recommendation = FootballIntelligenceService().recommend(
            context
        )
        self.assertFalse(recommendation.approved)

    def test_service_history_and_page(self):
        context = self.context()
        service = FootballIntelligenceService(
            safety_gate=TacticalRecommendationSafetyGate(
                minimum_confidence=0.50,
                maximum_risk=0.80,
            )
        )
        opinions, recommendation = service.recommend(context)

        with tempfile.TemporaryDirectory() as temp:
            repository = RecommendationHistoryRepository(
                Path(temp) / "recommendations.json"
            )
            repository.append(
                context.fixture_id,
                opinions,
                recommendation,
            )
            self.assertTrue(
                (Path(temp) / "recommendations.json").exists()
            )

        page = render_football_intelligence_page(
            opinions,
            recommendation,
        )
        self.assertIn("AI Football Intelligence", page)
        self.assertIn("Uzman ajan görüşleri", page)
        self.assertIn("Onaylandı", page)

if __name__ == "__main__":
    unittest.main()
