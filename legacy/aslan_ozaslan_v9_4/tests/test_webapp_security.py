import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.webapp import create_app

class WebAppSecurityTests(unittest.TestCase):
    def request(self, path, method="GET", headers=None):
        status = {}
        response_headers = {}
        environ = {"PATH_INFO": path, "REQUEST_METHOD": method}
        for key, value in (headers or {}).items():
            environ[key] = value

        def start_response(value, items):
            status["value"] = value
            response_headers.update(dict(items))

        body = b"".join(create_app()(environ, start_response))
        return status["value"], response_headers, body

    def test_analysis_requires_session(self):
        status, _, _ = self.request("/analysis")
        self.assertEqual(status, "401 Unauthorized")

    def test_run_requires_csrf(self):
        app = create_app()
        state = {}
        def start_response(value, items):
            state["status"] = value
        demo = json.loads(b"".join(app({"PATH_INFO":"/demo-session","REQUEST_METHOD":"GET"}, start_response)))
        body = b"".join(app(
            {
                "PATH_INFO":"/analysis/run",
                "REQUEST_METHOD":"POST",
                "HTTP_X_SESSION_TOKEN":demo["session_token"],
            },
            start_response,
        ))
        self.assertEqual(state["status"], "403 Forbidden")

if __name__ == "__main__":
    unittest.main()
