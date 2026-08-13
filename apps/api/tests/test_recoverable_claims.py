import json

from apps.api.app.maintenance_journal import (
    RedisMaintenanceJournal,
)

class Redis:
    def __init__(self):
        self.values = {
            "journal:claim:a": json.dumps({
                "claim_id": "a",
                "index_key": "index-a",
                "phase": "subject",
                "fencing_token": 3,
                "claimed_at": 10,
                "expires_at": 130,
                "status": "CLAIMED",
            })
        }

    def scan(self, cursor, match, count):
        return 0, list(self.values)

    def get(self, key):
        return self.values.get(key)

def test_recoverable_claim_listing():
    journal = RedisMaintenanceJournal(
        Redis(),
        prefix="journal",
    )

    claims = journal.recoverable_claims()

    assert len(claims) == 1
    assert claims[0].claim_id == "a"
    assert claims[0].index_key == "index-a"
