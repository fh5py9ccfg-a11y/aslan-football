import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.alerts import (
    Alert, AlertRouter, AlertSeverity, InMemoryAlertSink
)

class AlertRoutingTests(unittest.TestCase):
    def test_deduplicates_alerts(self):
        sink = InMemoryAlertSink()
        router = AlertRouter({AlertSeverity.CRITICAL: [sink]})
        alert = Alert(
            code="provider_down",
            severity=AlertSeverity.CRITICAL,
            message="Primary provider unavailable",
            deduplication_key="provider_down:primary",
        )
        self.assertTrue(router.route(alert))
        self.assertFalse(router.route(alert))
        self.assertEqual(len(sink.alerts), 1)

if __name__ == "__main__":
    unittest.main()
