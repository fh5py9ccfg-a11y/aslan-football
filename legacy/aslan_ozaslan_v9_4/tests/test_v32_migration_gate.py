import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.database.migration_gate import Migration, MigrationGate

class MigrationGateTests(unittest.TestCase):
    def test_irreversible_production_migration_is_blocked(self):
        report = MigrationGate().evaluate(
            applied_versions={1,2},
            pending=[
                Migration(3, "drop-old-column", False, "abc"),
            ],
            production=True,
        )
        self.assertFalse(report.allowed)
        self.assertIn("irreversible_in_production:3", report.blockers)

    def test_ordered_reversible_migrations_are_allowed(self):
        report = MigrationGate().evaluate(
            applied_versions={1},
            pending=[
                Migration(2, "add-index", True, "abc"),
                Migration(3, "add-table", True, "def"),
            ],
            production=True,
        )
        self.assertTrue(report.allowed)

if __name__ == "__main__":
    unittest.main()
