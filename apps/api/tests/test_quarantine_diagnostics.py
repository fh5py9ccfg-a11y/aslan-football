import json
from apps.api.app.quarantine_diagnostics import (
    RedisQuarantineDiagnosticService,
)

class Redis:
    def __init__(self):
        self.values = {
            "journal:quarantine:c1": json.dumps({
                "claim_id": "c1",
                "index_key": "index-a",
                "phase": "subject",
            })
        }
        self.sets = {"index-a": {"live", "orphan"}}
        self.ttls = {
            "index-a": -1,
            "session:live": 120,
            "session:orphan": -2,
        }

    def get(self, key):
        return self.values.get(key)

    def exists(self, key):
        return int(key in self.sets or key in self.values)

    def smembers(self, key):
        return self.sets.get(key, set())

    def ttl(self, key):
        return self.ttls.get(key, -2)

def test_diagnostic_counts_members():
    result = RedisQuarantineDiagnosticService(
        Redis(),
        session_prefix="session:",
        journal_prefix="journal",
    ).inspect("c1", now=100)

    assert result.member_count == 2
    assert result.live_members == 1
    assert result.orphan_members == 1
    assert result.recommended_action == "RETRY"
