import json

from apps.api.app.compensation_execution import (
    RedisCompensationExecutionRepository,
)

class Redis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def eval(self, script, number_of_keys, *args):
        key = args[0]
        now = int(args[1])
        payload = args[2]
        raw = self.values.get(key)
        if raw:
            current = json.loads(raw)
            if current["lease_expires_at"] > now:
                return [0, raw]
        self.values[key] = payload
        return [1, payload]

def test_expired_execution_can_be_taken_over():
    repo = RedisCompensationExecutionRepository(
        Redis(),
        prefix="exec",
        lease_seconds=10,
    )

    _, first = repo.claim(
        compensation_id="c1",
        owner="w1",
        now=0,
    )
    created, takeover = repo.claim(
        compensation_id="c1",
        owner="w2",
        now=11,
    )

    assert created is True
    assert takeover.owner == "w2"
    assert takeover.attempts == 2
