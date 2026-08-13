import hashlib
import hmac
import json

from apps.api.app.outbox_transport import (
    WebhookOutboxTransport,
)

def test_webhook_signature_is_stable():
    transport = WebhookOutboxTransport(
        url="https://example.test/hook",
        signing_secret="secret-at-least-sixteen",
        clock=lambda: 100,
    )
    body = json.dumps(
        {"a": 1},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    signature = transport._signature(
        timestamp="100",
        event_id="e1",
        body=body,
    )
    expected = hmac.new(
        b"secret-at-least-sixteen",
        b"100.e1." + body,
        hashlib.sha256,
    ).hexdigest()

    assert signature == expected
