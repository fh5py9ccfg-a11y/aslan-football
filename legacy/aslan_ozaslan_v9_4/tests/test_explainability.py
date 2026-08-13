import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.explainability import ExplanationFactor, ExplanationBuilder

class ExplainabilityTests(unittest.TestCase):
    def test_builds_ranked_explanation(self):
        explanation = ExplanationBuilder().build(
            probabilities=(0.55,0.25,0.20),
            factors=[
                ExplanationFactor("Form","HOME",0.6,"Son 5 maç"),
                ExplanationFactor("Kadro","AWAY",0.8,"Eksikler"),
            ],
            limitations=["Kadro kesinleşmedi"],
        )
        self.assertTrue(explanation.headline.startswith("En yüksek olasılık"))
        self.assertEqual(explanation.factors[0].name, "Kadro")
        self.assertEqual(explanation.limitations[0], "Kadro kesinleşmedi")

if __name__ == "__main__":
    unittest.main()
