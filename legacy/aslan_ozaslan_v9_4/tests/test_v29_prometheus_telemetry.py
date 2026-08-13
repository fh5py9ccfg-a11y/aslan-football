import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.metrics import PrometheusExporter, TelemetryBuffer

class PrometheusTelemetryTests(unittest.TestCase):
    def test_prometheus_export(self):
        text = PrometheusExporter().render({
            "jobs_processed_total": 4,
            "queue_depth": 2,
        })
        self.assertIn("jobs_processed_total 4.0", text)
        self.assertIn("queue_depth 2.0", text)

    def test_telemetry_buffer_is_bounded(self):
        buffer = TelemetryBuffer(max_events=2)
        buffer.emit("a", {})
        buffer.emit("b", {})
        buffer.emit("c", {})
        self.assertEqual([e.name for e in buffer.snapshot()], ["b", "c"])

if __name__ == "__main__":
    unittest.main()
