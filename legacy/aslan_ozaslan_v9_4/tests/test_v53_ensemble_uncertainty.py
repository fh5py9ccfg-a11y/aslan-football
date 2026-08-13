import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.football import (
    ModelProbability,
    WeightedEnsemble,
    PredictionUncertaintyAnalyzer,
)
from aslan_ozaslan.validation_v5 import (
    ModelValidationScore,
    ValidationWeightCalculator,
)

class EnsembleUncertaintyTests(unittest.TestCase):
    def test_validation_weights_sum_to_one(self):
        weights = ValidationWeightCalculator().calculate([
            ModelValidationScore("elo",0.50,0.90),
            ModelValidationScore("poisson",0.45,0.82),
        ])
        self.assertAlmostEqual(sum(item.weight for item in weights),1.0)

    def test_ensemble_and_uncertainty(self):
        prediction = WeightedEnsemble().combine([
            ModelProbability("elo",0.60,0.25,0.15,0.4),
            ModelProbability("poisson",0.50,0.30,0.20,0.6),
        ])
        self.assertAlmostEqual(prediction.home,0.54)
        uncertainty = PredictionUncertaintyAnalyzer().evaluate(
            prediction.home, prediction.draw, prediction.away
        )
        self.assertIn(uncertainty.confidence_label, {"HIGH","MEDIUM","LOW"})

if __name__ == "__main__":
    unittest.main()
