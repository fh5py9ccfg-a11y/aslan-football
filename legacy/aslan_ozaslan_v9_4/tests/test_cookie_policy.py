import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.security import CookiePolicy

class CookiePolicyTests(unittest.TestCase):
    def test_secure_cookie_header(self):
        header = CookiePolicy().header("abc")
        self.assertIn("HttpOnly", header)
        self.assertIn("Secure", header)
        self.assertIn("SameSite=Strict", header)

if __name__ == "__main__":
    unittest.main()
