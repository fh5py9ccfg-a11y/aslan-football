import json
from apps.api.app.quarantine_diagnostics import (
    RedisQuarantineDiagnosticService,
)
from apps.api.app.quarantine_retry import QuarantineRetryService

class Redis:
    def __init__(self):
        self.values = {
            "journal:quarantine:c1": json.dumps({
                "claim_id": "c1",
                "index_key": "index-a",
                "phase": "subject",
            })
        }

    def get(self, key):
        return self.values.get(key)

    def exists(self, key):
        raise RuntimeError("redis unavailable")

def test_diagnostic_error_returns_failed_retry():
    result = QuarantineRetryService(
        diagnostic_service=RedisQuarantineDiagnosticService(
            Redis(),
            journal_prefix="journal",
        ),
        maintainer_factory=lambda: None,
    ).retry(claim_id="c1", now=100)

    assert result.status == "FAILED"
    assert "redis unavailable" in result.error
