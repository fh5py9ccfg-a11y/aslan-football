import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.resilience import CircuitBreaker, CircuitState


class CircuitBreakerTests(unittest.TestCase):
    def test_opens_after_threshold(self):
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=60)
        breaker.record_failure()
        self.assertEqual(breaker.state, CircuitState.CLOSED)
        breaker.record_failure()
        self.assertEqual(breaker.state, CircuitState.OPEN)
        self.assertFalse(breaker.allow_request())

    def test_success_resets_breaker(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=60)
        breaker.record_failure()
        breaker.record_success()
        self.assertEqual(breaker.state, CircuitState.CLOSED)
        self.assertTrue(breaker.allow_request())


if __name__ == "__main__":
    unittest.main()
