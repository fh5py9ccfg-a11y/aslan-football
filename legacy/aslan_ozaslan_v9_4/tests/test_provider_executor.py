import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.providers import (
    ProviderError,
    ProviderResponse,
    SafeProviderExecutor,
)
from aslan_ozaslan.resilience import CircuitBreaker

class FakeClient:
    name = "fake"

    def __init__(self, fail=False, wrong_id=False):
        self.fail = fail
        self.wrong_id = wrong_id

    def fetch(self, resource_type, external_id):
        if self.fail:
            raise RuntimeError("network")
        return ProviderResponse(
            provider_name=self.name,
            resource_type=resource_type,
            external_id="wrong" if self.wrong_id else external_id,
            payload={"ok": True},
        )

class ProviderExecutorTests(unittest.TestCase):
    def test_successful_response(self):
        executor = SafeProviderExecutor(
            FakeClient(),
            CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=60),
        )
        result = executor.fetch("fixture", "fx-1")
        self.assertEqual(result.external_id, "fx-1")

    def test_wrong_external_id_is_rejected(self):
        executor = SafeProviderExecutor(
            FakeClient(wrong_id=True),
            CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=60),
        )
        with self.assertRaises(ProviderError):
            executor.fetch("fixture", "fx-1")

    def test_failures_open_circuit(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=60)
        executor = SafeProviderExecutor(FakeClient(fail=True), breaker)
        with self.assertRaises(ProviderError):
            executor.fetch("fixture", "fx-1")
        with self.assertRaises(ProviderError):
            executor.fetch("fixture", "fx-1")

if __name__ == "__main__":
    unittest.main()
