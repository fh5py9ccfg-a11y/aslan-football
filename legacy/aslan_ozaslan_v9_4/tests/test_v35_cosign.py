import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.security import CosignVerifier

class CosignTests(unittest.TestCase):
    def test_verified_signature(self):
        calls = []
        verifier = CosignVerifier(
            lambda image, identity, issuer: calls.append(
                (image, identity, issuer)
            ) or True,
            expected_identity="https://github.com/org/repo/.github/workflows/release.yml",
            expected_issuer="https://token.actions.githubusercontent.com",
        )
        image = "registry/app:3.5@" + "sha256:" + "b" * 64
        result = verifier.verify(image)
        self.assertTrue(result.verified)
        self.assertEqual(calls[0][0], image)

if __name__ == "__main__":
    unittest.main()
