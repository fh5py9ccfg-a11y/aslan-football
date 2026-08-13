import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import PrometheusSLOSource, SLOMeasurementService

class PrometheusSourceTests(unittest.TestCase):
    def test_availability_measurement(self):
        queries = []
        source = PrometheusSLOSource(
            query=lambda expression: queries.append(expression) or 0.9995
        )
        measurement = SLOMeasurementService(source).collect("availability", 30)
        self.assertEqual(measurement.achieved, 0.9995)
        self.assertIn("http_requests_total", queries[0])

if __name__ == "__main__":
    unittest.main()
