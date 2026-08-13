import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.decision_v6 import (
    DecisionContext,
    LiveSignalEngine,
    RiskOpportunityEvaluator,
    RealTimeDecisionEngine,
    DecisionHistoryRepository,
    LiveDecisionOrchestrator,
)
from aslan_ozaslan.live_v5 import (
    LiveProbabilityState,
    MomentumSnapshot,
)
from aslan_ozaslan.admin.decision_engine_page import (
    render_decision_engine_page,
)

class RealTimeDecisionTests(unittest.TestCase):
    def context(self):
        return DecisionContext(
            fixture_id="f1",
            minute=82,
            home_probability=0.68,
            draw_probability=0.20,
            away_probability=0.12,
            home_goals=2,
            away_goals=1,
            home_red_cards=0,
            away_red_cards=1,
            momentum_edge=2.2,
            reliability_score=0.88,
        )

    def test_signal_generation(self):
        signals = LiveSignalEngine().generate(self.context())
        types = {signal.signal_type for signal in signals}
        self.assertIn("PROBABILITY_EDGE", types)
        self.assertIn("MOMENTUM", types)
        self.assertIn("RED_CARD_ADVANTAGE", types)
        self.assertIn("LEAD_PROTECTION", types)

    def test_risk_and_opportunity(self):
        context = self.context()
        signals = LiveSignalEngine().generate(context)
        assessment = RiskOpportunityEvaluator().evaluate(
            context,
            signals,
        )
        self.assertGreater(assessment.opportunity_score, 0.5)
        self.assertGreaterEqual(assessment.risk_score, 0.0)
        self.assertEqual(assessment.dominant_side, "HOME")

    def test_engine_orchestrator_history_and_page(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = RealTimeDecisionEngine(
                latency_budget_ms=100.0
            )
            history = DecisionHistoryRepository(
                Path(temp) / "decisions.json"
            )
            orchestrator = LiveDecisionOrchestrator(
                engine=engine,
                history=history,
            )

            live_state = LiveProbabilityState(
                minute=82,
                home_probability=0.68,
                draw_probability=0.20,
                away_probability=0.12,
                home_goals=2,
                away_goals=1,
                home_red_cards=0,
                away_red_cards=1,
            )
            momentum = MomentumSnapshot(
                home_momentum=4.0,
                away_momentum=1.8,
                net_momentum=2.2,
                dominant_team="HOME",
            )

            report = orchestrator.on_live_state(
                fixture_id="f1",
                live_state=live_state,
                momentum=momentum,
                reliability_score=0.88,
            )

            self.assertEqual(
                report.snapshot.recommended_outcome,
                "HOME",
            )
            self.assertFalse(report.degraded)
            self.assertEqual(
                len(history.list_for_fixture("f1")),
                1,
            )

            page = render_decision_engine_page(report)
            self.assertIn("Real-Time Decision Engine", page)
            self.assertIn("Karar gecikmesi", page)
            self.assertIn("Sinyaller", page)

if __name__ == "__main__":
    unittest.main()
