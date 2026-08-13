import json

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
        if "heartbeat_at" in script:
            claim_key, fence_key = args[:2]
            token = int(args[2])
            owner = args[3]
            now = int(args[4])
            expires_at = int(args[5])
            raw = self.values[claim_key]
            data = json.loads(raw)
            if data["owner_id"] != owner:
                return [0, "owner"]
            data["heartbeat_at"] = now
            data["expires_at"] = expires_at
            payload = json.dumps(data)
            self.values[claim_key] = payload
            self.values[fence_key] = token
            return [1, payload]

        claim_key, fence_key = args[:2]
        payload = args[3]
        self.values[claim_key] = payload
        self.values[fence_key] = int(args[2])
        return [1, payload]

def test_claim_heartbeat_extends_expiry():
    redis = FakeRedis()
    journal = RedisMaintenanceJournal(
        redis,
        prefix="journal",
        fence_key="fence",
        claim_ttl_seconds=10,
    )
    claim = journal.claim(
        claim_id="c1",
        index_key="index",
        phase="subject",
        fencing_token=1,
        owner_id="owner-a",
        now=0,
    )

    renewed = journal.heartbeat(
        claim,
        now=8,
    )

    assert renewed.heartbeat_at == 8
    assert renewed.expires_at == 18
