import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.config import AppSettings, SettingsValidator

class SettingsTests(unittest.TestCase):
    def test_production_requires_secure_services(self):
        settings = AppSettings(
            environment="production",
            database_dsn="sqlite:///app.db",
            redis_url="",
            session_secret="short",
            backup_key="short",
            public_base_url="http://example.com",
        )
        errors = SettingsValidator().validate(settings)
        self.assertIn("production_database_must_be_postgresql", errors)
        self.assertIn("production_https_required", errors)

    def test_valid_production_settings(self):
        settings = AppSettings(
            environment="production",
            database_dsn="postgresql://u:p@db/app",
            redis_url="rediss://cache/0",
            session_secret="s" * 32,
            backup_key="b" * 32,
            public_base_url="https://aslan.example",
        )
        self.assertEqual(SettingsValidator().validate(settings), ())

if __name__ == "__main__":
    unittest.main()
