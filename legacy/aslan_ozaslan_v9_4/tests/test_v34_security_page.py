import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.security import (
    DependencyFinding,
    ImageScanResult,
    SupplyChainGate,
)
from aslan_ozaslan.admin import render_security_page

class SecurityPageTests(unittest.TestCase):
    def test_security_page_blocks_high_finding(self):
        scan = ImageScanResult(
            scanner_name="scanner",
            image_reference="image@sha256:" + "a" * 64,
            findings=(DependencyFinding("lib", "HIGH", "2.0"),),
        )
        gate = SupplyChainGate().evaluate(list(scan.findings))
        page = render_security_page(
            provenance_ok=True,
            scan_report=scan,
            supply_chain_report=gate,
        )
        self.assertIn("Release gate: Kapalı", page)
        self.assertIn("lib:HIGH", page)

if __name__ == "__main__":
    unittest.main()
