import json

from apps.api.app.compensation_outbox_publisher import (
    RedisOutboxDeliveryRepository,
)

class Redis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def eval(self, script, number_of_keys, *args):
        key = args[0]

        if "next_attempt_at" in script:
            now = int(args[1])
            payload = args[2]
            raw = self.values.get(key)
            if raw is not None:
                current = json.loads(raw)
                if current["status"] == "DELIVERED":
                    return [0, raw]
                if (
                    current["status"] == "IN_PROGRESS"
                    and current["lease_expires_at"] > now
                ):
                    return [0, raw]
            self.values[key] = payload
            return [1, payload]

        owner_token = args[1]
        payload = args[2]
        current = json.loads(self.values[key])
        if current["owner_token"] != owner_token:
            return [2, self.values[key]]
        self.values[key] = payload
        return [1, payload]

def test_delivery_claim_and_ack():
    repo = RedisOutboxDeliveryRepository(
        Redis(),
        prefix="delivery",
        lease_seconds=10,
    )

    created, record = repo.claim(
        event_id="e1",
        owner="publisher-a",
        now=0,
    )
    assert created is True

    delivered = repo.mark_delivered(
        record,
        now=1,
    )
    assert delivered.status == "DELIVERED"

    created, replay = repo.claim(
        event_id="e1",
        owner="publisher-b",
        now=20,
    )
    assert created is False
    assert replay.status == "DELIVERED"
