import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.calibration import TemperatureScaler

class CalibrationTests(unittest.TestCase):
    def test_sum_is_one(self):
        r = TemperatureScaler(1.5).transform((0.6,0.25,0.15))
        self.assertAlmostEqual(sum(r),1.0,places=7)

    def test_fit(self):
        t = TemperatureScaler().fit_grid(
            [(0.8,0.1,0.1),(0.7,0.2,0.1),(0.2,0.2,0.6)],[0,1,2])
        self.assertIn(t,(0.75,1.0,1.25,1.5,2.0))

if __name__ == "__main__":
    unittest.main()
