import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.providers import ProviderOrchestrator, ProviderUnavailable, RetryPolicy
from aslan_ozaslan.resilience import CircuitBreaker

class ProviderOrchestratorTests(unittest.TestCase):
    def test_fails_over_to_secondary_provider(self):
        orchestrator = ProviderOrchestrator(sleeper=lambda _: None)
        orchestrator.register(
            name="primary", priority=1,
            fetcher=lambda _: (_ for _ in ()).throw(ConnectionError("down")),
            retry_policy=RetryPolicy(max_attempts=1),
        )
        orchestrator.register(name="secondary", priority=2, fetcher=lambda _: {"ok": True})
        value, attempts = orchestrator.fetch("fx-1")
        self.assertEqual(value, {"ok": True})
        self.assertFalse(attempts[0].succeeded)
        self.assertTrue(attempts[1].succeeded)

    def test_raises_when_all_providers_fail(self):
        orchestrator = ProviderOrchestrator(sleeper=lambda _: None)
        orchestrator.register(
            name="only", priority=1,
            fetcher=lambda _: None,
            retry_policy=RetryPolicy(max_attempts=1),
        )
        with self.assertRaises(ProviderUnavailable):
            orchestrator.fetch("fx-2")

    def test_duplicate_provider_name_is_rejected(self):
        orchestrator = ProviderOrchestrator()
        orchestrator.register(name="a", priority=1, fetcher=lambda _: 1)
        with self.assertRaises(ValueError):
            orchestrator.register(name="a", priority=2, fetcher=lambda _: 2)

if __name__ == "__main__": unittest.main()
