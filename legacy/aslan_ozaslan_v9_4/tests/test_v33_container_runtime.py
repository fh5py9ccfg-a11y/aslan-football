import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import (
    ContainerImageValidator,
    RuntimeResources,
    RuntimePolicy,
    RuntimePolicyValidator,
)

class ContainerRuntimeTests(unittest.TestCase):
    def test_immutable_image(self):
        validator = ContainerImageValidator()
        image = validator.parse(
            "registry.example/aslan/app:3.3@" + "sha256:" + "a" * 64
        )
        validator.require_immutable(image)
        self.assertEqual(image.tag, "3.3")

    def test_latest_without_digest_is_rejected(self):
        validator = ContainerImageValidator()
        image = validator.parse("registry.example/aslan/app:latest")
        with self.assertRaises(ValueError):
            validator.require_immutable(image)

    def test_production_runtime_policy(self):
        policy = RuntimePolicy(
            replicas=2,
            max_unavailable=1,
            max_surge=1,
            resources=RuntimeResources(0.5, 1.0, 512, 1024),
            read_only_root_filesystem=True,
            run_as_non_root=True,
        )
        self.assertEqual(
            RuntimePolicyValidator().validate(policy, production=True),
            (),
        )

if __name__ == "__main__":
    unittest.main()
