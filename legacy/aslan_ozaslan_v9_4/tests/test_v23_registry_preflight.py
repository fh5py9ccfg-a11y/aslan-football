import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.model_registry import ModelRegistry
from aslan_ozaslan.operations import PreflightCheck, PreflightRunner

class RegistryPreflightTests(unittest.TestCase):
    def test_champion_rotation_and_release_block(self):
        registry = ModelRegistry()
        registry.register(version="v1",status="CHAMPION",trained_until="2026-06",
                          log_loss=.9,brier_score=.2,calibration_error=.04)
        registry.register(version="v2",status="CHAMPION",trained_until="2026-07",
                          log_loss=.8,brier_score=.19,calibration_error=.03)
        self.assertEqual(registry.champion().version,"v2")
        report = PreflightRunner().run([
            PreflightCheck("tests",True,True,"ok"),
            PreflightCheck("provider",False,True,"down"),
        ])
        self.assertFalse(report.ready)

if __name__ == "__main__":
    unittest.main()
