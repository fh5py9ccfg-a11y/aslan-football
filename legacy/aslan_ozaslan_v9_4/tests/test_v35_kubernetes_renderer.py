import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import (
    ClusterService,
    ClusterManifest,
    KubernetesManifestRenderer,
)

class KubernetesRendererTests(unittest.TestCase):
    def test_renderer_outputs_secure_deployment(self):
        image = "registry/aslan/app:3.5@" + "sha256:" + "a" * 64
        manifest = ClusterManifest(
            namespace="aslan-prod",
            services=(
                ClusterService("web", 2, image, 8000, "/health", "/health"),
            ),
        )
        bundle = KubernetesManifestRenderer().render(manifest)
        deployment = json.loads(bundle.deployments_json[0])
        security = deployment["spec"]["template"]["spec"]["containers"][0]["securityContext"]
        self.assertTrue(security["runAsNonRoot"])
        self.assertTrue(security["readOnlyRootFilesystem"])

if __name__ == "__main__":
    unittest.main()
