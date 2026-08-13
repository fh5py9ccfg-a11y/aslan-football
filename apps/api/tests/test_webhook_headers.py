from contextlib import contextmanager

from apps.api.app.outbox_transport import (
    WebhookOutboxTransport,
)

class Response:
    status = 202
    headers = {
        "X-Message-Id": "msg-1",
    }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

def test_webhook_sends_idempotency_and_signature_headers(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["headers"] = dict(request.header_items())
        return Response()

    monkeypatch.setattr(
        "urllib.request.urlopen",
        fake_urlopen,
    )

    transport = WebhookOutboxTransport(
        url="https://example.test/hook",
        signing_secret="secret-at-least-sixteen",
        clock=lambda: 100,
    )
    receipt = transport.publish(
        event_id="e1",
        payload={"a": 1},
    )

    headers = {
        key.lower(): value
        for key, value in captured["headers"].items()
    }
    assert headers["idempotency-key"] == "e1"
    assert headers["x-event-id"] == "e1"
    assert headers["x-webhook-timestamp"] == "100"
    assert headers["x-webhook-signature"].startswith("sha256=")
    assert receipt.external_id == "msg-1"
