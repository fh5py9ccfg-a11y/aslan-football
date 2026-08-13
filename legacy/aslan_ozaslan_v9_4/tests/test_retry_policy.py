import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.providers import RetryPolicy

class RetryPolicyTests(unittest.TestCase):
    def test_retries_then_succeeds(self):
        calls = {"count": 0}
        delays = []
        def operation():
            calls["count"] += 1
            if calls["count"] < 3:
                raise TimeoutError("geçici hata")
            return "ok"
        result = RetryPolicy(max_attempts=3, initial_delay_seconds=1, multiplier=2, max_delay_seconds=3).run(
            operation, sleeper=delays.append
        )
        self.assertEqual(result, "ok")
        self.assertEqual(delays, [1, 2])

    def test_does_not_retry_programming_error(self):
        calls = {"count": 0}
        def operation():
            calls["count"] += 1
            raise ValueError("kalıcı hata")
        with self.assertRaises(ValueError):
            RetryPolicy().run(operation, sleeper=lambda _: None)
        self.assertEqual(calls["count"], 1)

if __name__ == "__main__": unittest.main()
