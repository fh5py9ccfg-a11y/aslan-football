import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.alerts import Alert, AlertSeverity, WebhookAlertSink, EmailAlertSink

class AlertSinkTests(unittest.TestCase):
    def test_webhook_sink(self):
        captured = {}
        def sender(url, payload, headers):
            captured["url"] = url
            captured["payload"] = json.loads(payload)
            return 204
        sink = WebhookAlertSink(sender, "https://alerts.example")
        sink.send(Alert("provider_down", AlertSeverity.CRITICAL, "down", "k1"))
        self.assertEqual(captured["payload"]["severity"], "CRITICAL")

    def test_email_sink(self):
        messages = []
        EmailAlertSink(
            lambda recipient, subject, body: messages.append((recipient, subject, body)),
            "ops@example.com",
        ).send(Alert("drift", AlertSeverity.WARNING, "model drift", "k2"))
        self.assertIn("WARNING", messages[0][1])

if __name__ == "__main__":
    unittest.main()
