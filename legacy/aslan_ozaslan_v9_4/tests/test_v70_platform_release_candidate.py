import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.platform_v7 import (
    PlatformReadinessEvaluator,
    V7ReleaseGate,
    PlatformStatusService,
)
from aslan_ozaslan.admin.platform_v7_page import (
    render_platform_v7_page,
)

class PlatformV7Tests(unittest.TestCase):
    def test_readiness_blocks_missing_provider(self):
        readiness = PlatformReadinessEvaluator().evaluate(
            provider_configured=False,
            event_store_ready=True,
            decision_engine_ready=True,
            monitoring_ready=True,
            safe_mode=False,
        )
        self.assertFalse(readiness.production_ready)
        self.assertIn("provider_not_configured", readiness.blockers)

    def test_release_candidate_with_warning_only(self):
        readiness = PlatformReadinessEvaluator().evaluate(
            provider_configured=True,
            event_store_ready=True,
            decision_engine_ready=True,
            monitoring_ready=True,
            safe_mode=False,
        )
        decision = V7ReleaseGate().evaluate(
            tests_passed=True,
            readiness=readiness,
            minimum_test_count=250,
            observed_test_count=260,
            live_api_verified=False,
        )
        self.assertTrue(decision.approved)
        self.assertIn("live_api_not_yet_verified", decision.warnings)

        status = PlatformStatusService().build(
            readiness=readiness,
            test_count=260,
            active_fixture_count=0,
        )
        page = render_platform_v7_page(status, decision)
        self.assertIn("Aslan Özaslan v7.0 Release Candidate", page)
        self.assertIn("Release onayı", page)

    def test_safe_mode_blocks_release(self):
        readiness = PlatformReadinessEvaluator().evaluate(
            provider_configured=True,
            event_store_ready=True,
            decision_engine_ready=True,
            monitoring_ready=True,
            safe_mode=True,
        )
        decision = V7ReleaseGate().evaluate(
            tests_passed=True,
            readiness=readiness,
            minimum_test_count=250,
            observed_test_count=260,
            live_api_verified=True,
        )
        self.assertFalse(decision.approved)
        self.assertIn("safe_mode_active", decision.blockers)

if __name__ == "__main__":
    unittest.main()
