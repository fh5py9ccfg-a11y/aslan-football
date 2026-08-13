import json

from apps.api.app.idempotent_effects import (
    RedisIdempotentEffectRepository,
)

class Redis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def eval(self, script, number_of_keys, *args):
        key = args[0]
        if "existing.owner" in script:
            owner = args[1]
            payload = args[2]
            current = json.loads(self.values[key])
            if current["owner"] != owner:
                return [2, self.values[key]]
            self.values[key] = payload
            return [1, payload]
        payload = args[1]
        if key in self.values:
            return [0, self.values[key]]
        self.values[key] = payload
        return [1, payload]

def test_idempotent_effect_replays_completed_result():
    redis = Redis()
    repo = RedisIdempotentEffectRepository(
        redis,
        prefix="idem",
    )

    created, record = repo.claim(
        key="k1",
        operation="close",
        owner="owner",
        now=1,
    )
    assert created is True

    repo.complete(
        record=record,
        result_payload={"status": "CLOSED"},
        now=2,
    )

    created, replay = repo.claim(
        key="k1",
        operation="close",
        owner="other",
        now=3,
    )
    assert created is False
    assert replay.status == "COMPLETED"
    assert replay.result_payload == {"status": "CLOSED"}
