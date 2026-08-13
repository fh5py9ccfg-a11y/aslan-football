import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.security import (
    DependencyFinding,
    ImageScanRequest,
    ImageScanResult,
    ScannerService,
    ProvenanceVerifier,
)

class FakeScanner:
    name = "fake-scanner"
    def scan(self, request: ImageScanRequest):
        return ImageScanResult(
            scanner_name=self.name,
            image_reference=request.image_reference,
            findings=(DependencyFinding("lib", "LOW", None),),
        )

class ScannerProvenanceTests(unittest.TestCase):
    def test_scanner_requires_digest(self):
        with self.assertRaises(ValueError):
            ScannerService(FakeScanner()).scan("registry/app:3.4")

    def test_scanner_and_provenance(self):
        image = "registry/app:3.4@" + "sha256:" + "a" * 64
        result = ScannerService(FakeScanner()).scan(image)
        self.assertEqual(result.scanner_name, "fake-scanner")

        verifier = ProvenanceVerifier(b"k" * 32)
        provenance = verifier.sign(image, "ci-builder", "git-sha")
        self.assertTrue(verifier.verify(provenance))

if __name__ == "__main__":
    unittest.main()
