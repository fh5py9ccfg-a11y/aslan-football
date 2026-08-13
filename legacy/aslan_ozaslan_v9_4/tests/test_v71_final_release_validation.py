import sys, unittest, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.release_v7 import (
    SecretInspector,
    SmokeCheck,
    SmokeTestReport,
    ProductionEnvironmentInput,
    ProductionEnvironmentAuditor,
    FinalV7ReleaseGate,
    ReleaseChecklistItem,
    ReleaseChecklist,
)
from aslan_ozaslan.platform_v7 import PlatformReadinessEvaluator
from aslan_ozaslan.admin.final_release_page import render_final_release_page

class FinalReleaseValidationTests(unittest.TestCase):
    def test_secret_inspector(self):
        os.environ["SPORTMONKS_API_TOKEN"] = "secret"
        inspector = SecretInspector()
        status = inspector.inspect_environment("SPORTMONKS_API_TOKEN")
        self.assertTrue(status.available)
        self.assertEqual(inspector.require("SPORTMONKS_API_TOKEN"), "secret")
        del os.environ["SPORTMONKS_API_TOKEN"]

    def test_environment_auditor_blocks_missing_controls(self):
        report = ProductionEnvironmentAuditor().audit(
            ProductionEnvironmentInput(
                https_enabled=True,
                secure_secrets=False,
                database_backup_ready=True,
                monitoring_ready=True,
                alerting_ready=False,
                provider_token_available=False,
                rollback_ready=True,
            )
        )
        self.assertFalse(report.ready)
        self.assertIn("secure_secret_storage_missing", report.blockers)
        self.assertIn("provider_token_missing", report.blockers)
        self.assertIn("alerting_not_ready", report.warnings)

    def test_final_gate_approves_complete_release(self):
        smoke = SmokeTestReport(
            passed=True,
            checks=(
                SmokeCheck("provider_config", True, 1.0, "token_available"),
                SmokeCheck("provider_fixture_fetch", True, 5.0, "fixture_received"),
                SmokeCheck("event_store", True, 1.0, "ready"),
                SmokeCheck("decision_engine", True, 1.0, "ready"),
            ),
            provider_verified=True,
        )
        environment = ProductionEnvironmentAuditor().audit(
            ProductionEnvironmentInput(
                https_enabled=True,
                secure_secrets=True,
                database_backup_ready=True,
                monitoring_ready=True,
                alerting_ready=True,
                provider_token_available=True,
                rollback_ready=True,
            )
        )
        platform = PlatformReadinessEvaluator().evaluate(
            provider_configured=True,
            event_store_ready=True,
            decision_engine_ready=True,
            monitoring_ready=True,
            safe_mode=False,
        )
        decision = FinalV7ReleaseGate().evaluate(
            test_count=262,
            minimum_test_count=250,
            smoke_report=smoke,
            environment_report=environment,
            platform_readiness=platform,
        )
        self.assertTrue(decision.approved)
        self.assertEqual(decision.version, "7.0-final")

        page = render_final_release_page(decision, smoke, environment)
        self.assertIn("Final v7 Release Validation", page)
        self.assertIn("Provider verified", page)

    def test_release_checklist(self):
        missing = ReleaseChecklist().evaluate((
            ReleaseChecklistItem("tests", True, True),
            ReleaseChecklistItem("provider smoke", False, True),
            ReleaseChecklistItem("docs", False, False),
        ))
        self.assertEqual(missing, ("provider smoke",))

if __name__ == "__main__":
    unittest.main()
