import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.integration_v6 import (
    ProviderFixtureSnapshot,
)
from aslan_ozaslan.integration_v6.provider_events import (
    ProviderEventRecord,
    ProviderEventMapper,
)
from aslan_ozaslan.integration_v6.event_repository import (
    ProviderEventRepository,
)
from aslan_ozaslan.integration_v6.reconciliation import (
    SnapshotEventReconciler,
)
from aslan_ozaslan.integration_v6.late_event import LateEventPolicy
from aslan_ozaslan.integration_v6.event_orchestrator import (
    ProviderEventOrchestrator,
)
from aslan_ozaslan.live_v5 import (
    LiveProbabilityState,
    LiveMatchProcessor,
)
from aslan_ozaslan.admin.provider_event_page import (
    render_provider_event_page,
)

class ProviderEventTests(unittest.TestCase):
    def snapshot(self, home_score=1, away_score=0, minute=40):
        return ProviderFixtureSnapshot(
            fixture_id="f1",
            minute=minute,
            home_team_id="home",
            away_team_id="away",
            home_score=home_score,
            away_score=away_score,
            state="LIVE",
            updated_at="2026-07-31T21:00:00+00:00",
        )

    def event(self, event_id="e1", minute=35, corrected=False, cancelled=False):
        return ProviderEventRecord(
            provider_event_id=event_id,
            fixture_id="f1",
            minute=minute,
            team_id="home",
            event_type="goal",
            corrected=corrected,
            cancelled=cancelled,
        )

    def test_mapper_and_late_policy(self):
        mapped = ProviderEventMapper().map(self.event())
        self.assertEqual(mapped.event_type, "GOAL")

        late = LateEventPolicy(allowed_lateness_minutes=3).evaluate(
            self.event(minute=30),
            current_minute=40,
        )
        self.assertTrue(late.late)
        self.assertTrue(late.requires_replay)

    def test_repository_and_reconciliation(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = ProviderEventRepository(Path(temp) / "events.json")
            self.assertTrue(repo.upsert(self.event()))
            self.assertFalse(repo.upsert(self.event()))

            report = SnapshotEventReconciler().reconcile(
                self.snapshot(),
                repo.for_fixture("f1"),
            )
            self.assertTrue(report.consistent)

            mismatch = SnapshotEventReconciler().reconcile(
                self.snapshot(home_score=2),
                repo.for_fixture("f1"),
            )
            self.assertFalse(mismatch.consistent)
            self.assertIn("home_goal_mismatch", mismatch.issues)

    def test_orchestrator_and_page(self):
        with tempfile.TemporaryDirectory() as temp:
            processor = LiveMatchProcessor(
                home_team_id="home",
                away_team_id="away",
                initial_state=LiveProbabilityState(
                    minute=0,
                    home_probability=0.45,
                    draw_probability=0.30,
                    away_probability=0.25,
                    home_goals=0,
                    away_goals=0,
                    home_red_cards=0,
                    away_red_cards=0,
                ),
            )
            orchestrator = ProviderEventOrchestrator(
                repository=ProviderEventRepository(
                    Path(temp) / "events.json"
                ),
                live_processor=processor,
            )
            record = self.event()
            update = orchestrator.process(
                snapshot=self.snapshot(),
                record=record,
            )
            self.assertTrue(update.accepted)
            self.assertTrue(update.changed)
            self.assertTrue(update.reconciliation_consistent)
            self.assertGreater(processor.state.home_probability, 0.45)

            duplicate = orchestrator.process(
                snapshot=self.snapshot(),
                record=record,
            )
            self.assertFalse(duplicate.changed)

            page = render_provider_event_page(update, record)
            self.assertIn("Provider Event Reconciliation", page)
            self.assertIn("Snapshot ile tutarlı", page)

if __name__ == "__main__":
    unittest.main()
