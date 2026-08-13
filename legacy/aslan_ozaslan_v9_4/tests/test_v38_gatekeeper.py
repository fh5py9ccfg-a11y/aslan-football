import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.policy import (
    GatekeeperConstraint,
    GatekeeperRenderer,
    immutable_image_rego,
)

class GatekeeperTests(unittest.TestCase):
    def test_template_and_constraint(self):
        renderer = GatekeeperRenderer()
        template = json.loads(renderer.render_template(
            name="K8sImmutableImage",
            rego=immutable_image_rego(),
        ))
        constraint = json.loads(renderer.render_constraint(
            GatekeeperConstraint(
                name="require-image-digest",
                kind="K8sImmutableImage",
                message="digest required",
                parameters={},
            )
        ))
        self.assertEqual(template["kind"], "ConstraintTemplate")
        self.assertEqual(constraint["kind"], "K8sImmutableImage")

if __name__ == "__main__":
    unittest.main()
