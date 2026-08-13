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
        self.sets = {"index-a": {"orphan"}}
        self.ttls = {
            "index-a": -1,
            "session:orphan": -2,
        }

    def get(self, key):
        return self.values.get(key)

    def exists(self, key):
        return int(key in self.sets or key in self.values)

    def smembers(self, key):
        return set(self.sets.get(key, set()))

    def ttl(self, key):
        return self.ttls.get(key, -2)

    def srem(self, key, value):
        self.sets[key].discard(value)
        return 1

    def delete(self, key):
        self.sets.pop(key, None)
        return 1

class Maintainer:
    def __init__(self, redis):
        self.redis = redis

    def _clean_index(self, key):
        removed = 0
        for member in list(self.redis.smembers(key)):
            if self.redis.ttl(f"session:{member}") <= 0:
                removed += self.redis.srem(key, member)
        if not self.redis.smembers(key):
            self.redis.delete(key)
        return removed, 0

def test_retry_repairs_quarantined_index():
    redis = Redis()
    service = QuarantineRetryService(
        diagnostic_service=RedisQuarantineDiagnosticService(
            redis,
            session_prefix="session:",
            journal_prefix="journal",
        ),
        maintainer_factory=lambda: Maintainer(redis),
    )

    result = service.retry(claim_id="c1", now=100)
    assert result.status == "SUCCEEDED"
    assert result.removed == 1
    assert "index-a" not in redis.sets
