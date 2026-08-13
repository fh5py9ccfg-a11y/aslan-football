import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.providers_v6 import NormalizedLiveFixture
from aslan_ozaslan.integration_v6 import (
    ProviderFixtureSnapshot,
    FixtureStateGuard,
    SnapshotEventDeriver,
    FixtureSnapshotRepository,
    ProviderToAnalyticsOrchestrator,
    SportmonksAnalyticsBridge,
)
from aslan_ozaslan.admin.live_integration_page import (
    render_live_integration_page,
)

class ProviderAnalyticsIntegrationTests(unittest.TestCase):
    def snapshot(self, minute=10, home_score=0, away_score=0):
        return ProviderFixtureSnapshot(
            fixture_id="f1",
            minute=minute,
            home_team_id="home",
            away_team_id="away",
            home_score=home_score,
            away_score=away_score,
            state="LIVE",
            updated_at="2026-07-31T20:00:00+00:00",
        )

    def test_state_guard_rejects_regression(self):
        guard = FixtureStateGuard()
        previous = self.snapshot(minute=30, home_score=1)
        current = self.snapshot(minute=25, home_score=1)
        decision = guard.evaluate(current, previous)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "stale_minute")

    def test_event_derivation(self):
        previous = self.snapshot(minute=20, home_score=0, away_score=0)
        current = self.snapshot(minute=25, home_score=1, away_score=0)
        events = SnapshotEventDeriver().derive(current, previous)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "GOAL")
        self.assertEqual(events[0].team_id, "home")

    def test_bridge_and_orchestrator(self):
        with tempfile.TemporaryDirectory() as temp:
            bridge = SportmonksAnalyticsBridge()
            normalized = NormalizedLiveFixture(
                provider_fixture_id="f1",
                state="LIVE",
                minute=12,
                home_team_id="home",
                away_team_id="away",
                home_score=0,
                away_score=0,
                raw={},
            )
            first_snapshot = bridge.to_snapshot(normalized)

            repository = FixtureSnapshotRepository(
                Path(temp) / "fixtures.json"
            )
            orchestrator = ProviderToAnalyticsOrchestrator(
                repository=repository
            )
            first = orchestrator.process(first_snapshot)
            self.assertTrue(first.accepted)
            self.assertEqual(first.event_count, 0)

            second_snapshot = self.snapshot(
                minute=30,
                home_score=1,
                away_score=0,
            )
            second = orchestrator.process(second_snapshot)
            self.assertTrue(second.accepted)
            self.assertEqual(second.event_count, 1)
            self.assertGreater(second.home_probability, 0.45)
            self.assertAlmostEqual(
                second.home_probability
                + second.draw_probability
                + second.away_probability,
                1.0,
            )

            page = render_live_integration_page(
                second,
                second_snapshot,
            )
            self.assertIn("Provider → Live Analytics", page)
            self.assertIn("Türetilen event", page)

if __name__ == "__main__":
    unittest.main()
