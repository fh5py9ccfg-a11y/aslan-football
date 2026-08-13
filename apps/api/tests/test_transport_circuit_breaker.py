from apps.api.app.transport_circuit_breaker import (
    CircuitOpen,
    RedisCircuitBreaker,
)

class Redis:
    def __init__(self):
        self.values = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

def test_circuit_opens_and_half_opens():
    breaker = RedisCircuitBreaker(
        Redis(),
        name="webhook",
        failure_threshold=2,
        recovery_timeout_seconds=10,
    )

    breaker.record_failure("one", now=0)
    state = breaker.record_failure("two", now=1)

    assert state.state == "OPEN"

    try:
        breaker.before_call(now=5)
        assert False, "CircuitOpen bekleniyordu"
    except CircuitOpen:
        pass

    probe = breaker.before_call(now=11)
    assert probe.state == "HALF_OPEN"

    closed = breaker.record_success(now=12)
    assert closed.state == "CLOSED"
    assert closed.failures == 0
