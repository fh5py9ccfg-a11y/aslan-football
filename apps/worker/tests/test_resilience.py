import pytest
from worker_app.resilience import CircuitBreaker

def test_circuit_breaker_opens_and_recovers():
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout_seconds=10,
    )
    breaker.record_failure(now=100)
    assert breaker.snapshot().state == "CLOSED"

    breaker.record_failure(now=101)
    assert breaker.snapshot().state == "OPEN"

    with pytest.raises(RuntimeError):
        breaker.before_call(now=105)

    breaker.before_call(now=111)
    assert breaker.snapshot().state == "HALF_OPEN"

    breaker.record_success()
    assert breaker.snapshot().state == "CLOSED"
