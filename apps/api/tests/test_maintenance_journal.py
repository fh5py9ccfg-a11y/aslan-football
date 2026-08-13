import json
import pytest

from apps.api.app.distributed_lease import (
    StaleFencingToken,
)
from apps.api.app.maintenance_journal import (
    RedisMaintenanceJournal,
)

class FakeRedis:
    def __init__(self):
        self.values = {}

    def eval(self, script, number_of_keys, *args):
        if "completed_payload" in script:
            claim_key, done_key, fence_key = args[:3]
            token, payload = int(args[3]), args[4]
            current = int(self.values.get(fence_key, 0))
            if token < current:
                return [-1, current]
            self.values[fence_key] = token
            self.values[done_key] = payload
            self.values.pop(claim_key, None)
            return [1, token]

        claim_key, fence_key = args[:2]
        token, payload = int(args[2]), args[3]
        current = int(self.values.get(fence_key, 0))
        if token < current:
            return [-1, current]
        if claim_key in self.values:
            return [0, self.values[claim_key]]
        self.values[fence_key] = token
        self.values[claim_key] = payload
        return [1, payload]

    def exists(self, key):
        return int(key in self.values)

    def scan(self, cursor, match, count):
        keys = [
            key for key in self.values
            if ":claim:" in key
        ]
        return 0, keys

    def get(self, key):
        return self.values.get(key)

def test_claim_complete_and_stale_rejection():
    redis = FakeRedis()
    journal = RedisMaintenanceJournal(
        redis,
        prefix="journal",
        fence_key="fence",
    )

    claim = journal.claim(
        claim_id="c1",
        index_key="index-1",
        phase="subject",
        fencing_token=5,
        now=10,
    )
    assert claim is not None

    duplicate = journal.claim(
        claim_id="c1",
        index_key="index-1",
        phase="subject",
        fencing_token=5,
        now=11,
    )
    assert duplicate is None

    journal.complete(
        claim=claim,
        removed=2,
        repaired=1,
        completed_at=12,
    )
    assert journal.is_completed("c1") is True
    assert journal.recoverable_claims() == ()

    with pytest.raises(StaleFencingToken):
        journal.claim(
            claim_id="c2",
            index_key="index-2",
            phase="family",
            fencing_token=4,
            now=20,
        )
