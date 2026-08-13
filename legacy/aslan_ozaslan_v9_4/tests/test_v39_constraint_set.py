import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.policy import ProductionConstraintSetFactory

class ConstraintSetTests(unittest.TestCase):
    def test_production_constraint_set(self):
        constraint_set = ProductionConstraintSetFactory().build()
        kinds = {item.kind for item in constraint_set.constraints}
        self.assertIn("K8sImmutableImage", kinds)
        self.assertIn("K8sRequireNonRoot", kinds)
        self.assertIn("K8sResourceLimits", kinds)

if __name__ == "__main__":
    unittest.main()
