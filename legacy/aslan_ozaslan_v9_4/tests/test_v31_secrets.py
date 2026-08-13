import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.config import RequiredSecret, SecretResolver

class FakeProvider:
    def __init__(self, values):
        self.values = values
    def get(self, name):
        return self.values.get(name)

class SecretsTests(unittest.TestCase):
    def test_required_secrets(self):
        resolver = SecretResolver(FakeProvider({
            "SESSION_SECRET": "x" * 32,
            "BACKUP_KEY": "y" * 32,
        }))
        values = resolver.require([
            RequiredSecret("SESSION_SECRET", 32),
            RequiredSecret("BACKUP_KEY", 32),
        ])
        self.assertEqual(len(values), 2)

    def test_weak_secret_is_rejected(self):
        resolver = SecretResolver(FakeProvider({"SESSION_SECRET": "short"}))
        with self.assertRaises(ValueError):
            resolver.require([RequiredSecret("SESSION_SECRET", 32)])

if __name__ == "__main__":
    unittest.main()
