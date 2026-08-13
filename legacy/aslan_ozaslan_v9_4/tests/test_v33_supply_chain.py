import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.security import DependencyFinding, SupplyChainGate

class SupplyChainTests(unittest.TestCase):
    def test_high_vulnerability_blocks_release(self):
        report = SupplyChainGate().evaluate([
            DependencyFinding("example-lib", "HIGH", "2.0.1"),
            DependencyFinding("minor-lib", "LOW", None),
        ])
        self.assertFalse(report.allowed)
        self.assertIn("example-lib:HIGH", report.blockers)

if __name__ == "__main__":
    unittest.main()
