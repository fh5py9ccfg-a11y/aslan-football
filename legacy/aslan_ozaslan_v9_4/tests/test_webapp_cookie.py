import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.webapp import create_app

class WebAppCookieTests(unittest.TestCase):
    def test_demo_session_sets_secure_cookie(self):
        state = {}
        def start_response(status, headers):
            state["status"] = status
            state["headers"] = dict(headers)
        body = b"".join(create_app()(
            {"PATH_INFO":"/demo-session","REQUEST_METHOD":"GET"},
            start_response
        ))
        self.assertEqual(state["status"], "200 OK")
        self.assertIn("Set-Cookie", state["headers"])
        self.assertIn("HttpOnly", state["headers"]["Set-Cookie"])

if __name__ == "__main__":
    unittest.main()
