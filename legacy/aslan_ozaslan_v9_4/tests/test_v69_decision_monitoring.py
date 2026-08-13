import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.monitoring_v6 import (
    DecisionQualitySample,
    DecisionQualityWindow,
    DecisionDriftDetector,
    DecisionCircuitBreaker,
    DecisionMonitoringAggregator,
    MonitoringHistoryRepository,
)
from aslan_ozaslan.admin.monitoring_page import (
    render_monitoring_page,
)

class DecisionMonitoringTests(unittest.TestCase):
    def sample(
        self,
        confidence,
        risk,
        latency,
        degraded=False,
        minute=60,
    ):
        return DecisionQualitySample(
            fixture_id="f1",
            minute=minute,
            confidence=confidence,
            risk_score=risk,
            opportunity_score=0.70,
            latency_ms=latency,
            degraded=degraded,
        )

    def test_quality_window_is_bounded(self):
        window = DecisionQualityWindow(capacity=2)
        window.add(self.sample(0.8, 0.2, 10))
        window.add(self.sample(0.7, 0.3, 20))
        window.add(self.sample(0.6, 0.4, 30))
        self.assertEqual(len(window), 2)
        self.assertEqual(window.samples()[0].confidence, 0.7)

    def test_drift_detector(self):
        baseline = tuple(
            self.sample(0.82, 0.20, 12)
            for _ in range(5)
        )
        recent = tuple(
            self.sample(0.58, 0.45, 60, degraded=True)
            for _ in range(5)
        )
        report = DecisionDriftDetector().detect(
            baseline,
            recent,
        )
        self.assertTrue(report.detected)
        self.assertIn("confidence_drop", report.reasons)
        self.assertIn("risk_increase", report.reasons)
        self.assertIn("latency_regression", report.reasons)

    def test_circuit_safe_mode_aggregator_page_and_history(self):
        baseline = tuple(
            self.sample(0.82, 0.20, 12)
            for _ in range(5)
        )
        recent = tuple(
            self.sample(0.58, 0.45, 60, degraded=True)
            for _ in range(5)
        )

        breaker = DecisionCircuitBreaker(
            failure_threshold=1,
            degraded_ratio_threshold=0.40,
        )
        aggregator = DecisionMonitoringAggregator(
            circuit_breaker=breaker
        )
        snapshot, drift, safe_mode = aggregator.build(
            baseline=baseline,
            recent=recent,
        )

        self.assertTrue(snapshot.drift_detected)
        self.assertTrue(snapshot.circuit_open)
        self.assertTrue(snapshot.safe_mode)
        self.assertNotIn(
            "LIVE_DECISION_SUPPORT",
            safe_mode.allowed_actions,
        )

        with tempfile.TemporaryDirectory() as temp:
            repository = MonitoringHistoryRepository(
                Path(temp) / "monitoring.json"
            )
            repository.append(snapshot, drift, safe_mode)
            self.assertTrue(
                (Path(temp) / "monitoring.json").exists()
            )

        page = render_monitoring_page(
            snapshot,
            drift,
            safe_mode,
        )
        self.assertIn("Real-Time Decision Monitoring", page)
        self.assertIn("Safe mode", page)
        self.assertIn("Drift nedenleri", page)

if __name__ == "__main__":
    unittest.main()
