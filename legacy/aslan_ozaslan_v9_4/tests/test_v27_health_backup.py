import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import HealthMonitor, FileBackupService

class HealthBackupTests(unittest.TestCase):
    def test_critical_health_failure(self):
        report = HealthMonitor().run({
            "database": (lambda: False, True),
            "banner": (lambda: False, False),
        })
        self.assertFalse(report.healthy)
        self.assertTrue(report.degraded)

    def test_backup_and_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "app.db"
            target = Path(directory) / "backup" / "app.db"
            source.write_bytes(b"database")
            service = FileBackupService()
            result = service.backup(source, target)
            self.assertTrue(service.verify(result))

if __name__ == "__main__":
    unittest.main()
