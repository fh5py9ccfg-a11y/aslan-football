import urllib.error

from apps.api.app.outbox_transport import (
    WebhookOutboxTransport,
)
from apps.api.app.transport_circuit_breaker import (
    RedisCircuitBreaker,
)

class Redis:
    def __init__(self):
        self.values = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

def test_webhook_failure_updates_circuit(monkeypatch):
    redis = Redis()
    breaker = RedisCircuitBreaker(
        redis,
        name="webhook",
        failure_threshold=1,
        recovery_timeout_seconds=10,
    )
    transport = WebhookOutboxTransport(
        url="https://example.test/hook",
        circuit_breaker=breaker,
        clock=lambda: 100,
    )

    def fail(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(
        "urllib.request.urlopen",
        fail,
    )

    try:
        transport.publish(
            event_id="e1",
            payload={"a": 1},
        )
        assert False, "URLError bekleniyordu"
    except urllib.error.URLError:
        pass

    state = breaker.get()
    assert state.state == "OPEN"
    assert state.failures == 1
