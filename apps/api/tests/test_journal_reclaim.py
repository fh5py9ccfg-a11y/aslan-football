from apps.api.app.maintenance_journal import (
    RedisMaintenanceJournal,
)

class FakeRedis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def exists(self, key):
        return int(key in self.values)

    def eval(self, script, number_of_keys, *args):
        if "local now" in script:
            claim_key, fence_key = args[:2]
            token = int(args[2])
            payload = args[3]
            now = int(args[5])
            existing = self.values.get(claim_key)
            if existing is not None:
                import json
                current = json.loads(existing)
                if int(current["expires_at"]) > now:
                    return [0, existing]
            self.values[fence_key] = token
            self.values[claim_key] = payload
            return [1, payload]
        raise AssertionError("Unexpected script")

def test_expired_claim_can_be_reclaimed():
    redis = FakeRedis()
    journal = RedisMaintenanceJournal(
        redis,
        prefix="journal",
        fence_key="fence",
        claim_ttl_seconds=10,
    )

    first = journal.claim(
        claim_id="c1",
        index_key="index",
        phase="subject",
        fencing_token=1,
        owner_id="owner-a",
        now=0,
    )
    assert first is not None
    assert first.attempts == 1

    blocked = journal.claim(
        claim_id="c1",
        index_key="index",
        phase="subject",
        fencing_token=1,
        owner_id="owner-b",
        now=5,
    )
    assert blocked is None

    reclaimed = journal.claim(
        claim_id="c1",
        index_key="index",
        phase="subject",
        fencing_token=2,
        owner_id="owner-b",
        now=11,
    )
    assert reclaimed is not None
    assert reclaimed.owner_id == "owner-b"
    assert reclaimed.attempts == 2
