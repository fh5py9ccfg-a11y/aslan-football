import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.webapp import create_app

class WebAppTests(unittest.TestCase):
    def request(self, path):
        status = {}
        headers = {}
        def start_response(value, response_headers):
            status["value"] = value
            headers.update(dict(response_headers))
        body = b"".join(
            create_app()(
                {"PATH_INFO": path, "REQUEST_METHOD": "GET"},
                start_response,
            )
        )
        return status["value"], headers, body

    def test_home_page(self):
        status, headers, body = self.request("/")
        self.assertEqual(status, "200 OK")
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn("Aslan", body.decode("utf-8"))

    def test_health_endpoint(self):
        status, headers, body = self.request("/health")
        self.assertEqual(status, "200 OK")
        self.assertIn('"status": "ok"', body.decode("utf-8"))

    def test_not_found(self):
        status, _, _ = self.request("/missing")
        self.assertEqual(status, "404 Not Found")

if __name__ == "__main__":
    unittest.main()
