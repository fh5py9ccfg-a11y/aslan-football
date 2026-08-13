from apps.api.app.cache_resilience import (
    MetadataCircuitBreaker,
)

def test_metadata_circuit_breaker():
    breaker = MetadataCircuitBreaker(
        failure_threshold=2,
        recovery_timeout_seconds=10,
    )

    assert breaker.allow(now=0) is True
    breaker.failure(now=1)
    breaker.failure(now=2)
    assert breaker.state == "OPEN"
    assert breaker.allow(now=5) is False
    assert breaker.allow(now=12) is True
    assert breaker.state == "HALF_OPEN"

    breaker.success()
    assert breaker.state == "CLOSED"
