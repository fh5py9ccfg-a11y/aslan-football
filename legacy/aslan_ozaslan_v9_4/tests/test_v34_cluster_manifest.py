import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import (
    ClusterService,
    ClusterManifest,
    ClusterManifestValidator,
)

class ClusterManifestTests(unittest.TestCase):
    def test_valid_production_manifest(self):
        image = "registry/aslan/app:3.4@" + "sha256:" + "b" * 64
        manifest = ClusterManifest(
            namespace="aslan-production",
            services=(
                ClusterService("web", 2, image, 8000, "/health", "/health"),
                ClusterService("worker", 2, image, 9000, "/ready", "/live"),
            ),
        )
        self.assertEqual(
            ClusterManifestValidator().validate(manifest, production=True),
            (),
        )

    def test_digest_is_required(self):
        manifest = ClusterManifest(
            namespace="aslan",
            services=(
                ClusterService("web", 2, "registry/app:3.4", 8000, "/health", "/health"),
            ),
        )
        errors = ClusterManifestValidator().validate(manifest, production=True)
        self.assertIn("image_digest_required:web", errors)

if __name__ == "__main__":
    unittest.main()
