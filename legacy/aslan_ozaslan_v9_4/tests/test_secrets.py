import os, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.secrets import EnvironmentSecretProvider

class SecretTests(unittest.TestCase):
    def test_required_secret_is_read(self):
        os.environ["TEST_SECRET"] = " value "
        self.assertEqual(EnvironmentSecretProvider().get_required("TEST_SECRET"), "value")

    def test_missing_required_secret_raises(self):
        os.environ.pop("MISSING_SECRET", None)
        with self.assertRaises(RuntimeError):
            EnvironmentSecretProvider().get_required("MISSING_SECRET")

if __name__ == "__main__":
    unittest.main()
