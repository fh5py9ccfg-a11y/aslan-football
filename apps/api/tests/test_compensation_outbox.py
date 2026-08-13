import json
from dataclasses import dataclass

from apps.api.app.compensation_outbox import (
    RedisCompensationCommitter,
)

@dataclass
class Compensation:
    compensation_id: str = "c1"
    request_id: str = "r1"
    claim_id: str = "q1"
    action: str = "ACTION"
    status: str = "PENDING"
    reason: str = ""
    created_at: int = 1
    completed_at: int | None = None
    attempts: int = 0
    next_attempt_at: int | None = 1

@dataclass
class Execution:
    compensation_id: str = "c1"
    owner: str = "worker"
    owner_token: str = "token"
    status: str = "IN_PROGRESS"
    claimed_at: int = 1
    heartbeat_at: int = 1
    lease_expires_at: int = 61
    attempts: int = 1

class Redis:
    def __init__(self):
        self.values = {
            "exec:c1": json.dumps(Execution().__dict__),
        }
        self.sets = {
            "comp:status:PENDING": {"c1"},
        }

    def eval(self, script, number_of_keys, *args):
        comp_key, exec_key, outbox_key, old_key, new_key, sequence_key = args[:6]
        owner_token = args[6]
        current = json.loads(self.values[exec_key])
        if current["owner_token"] != owner_token:
            return [2, self.values[exec_key]]
        sequence = int(self.values.get(sequence_key, 0)) + 1
        self.values[sequence_key] = sequence
        event = json.loads(args[9])
        event["sequence"] = sequence
        payload = json.dumps(event)
        self.values[comp_key] = args[7]
        self.values[exec_key] = args[8]
        self.values[outbox_key] = payload
        self.sets.setdefault(old_key, set()).discard(args[10])
        self.sets.setdefault(new_key, set()).add(args[10])
        return [1, payload]

    def scan(self, cursor, match, count):
        return 0, [k for k in self.values if k.startswith("outbox:")]

    def get(self, key):
        return self.values.get(key)

def test_atomic_success_commit_writes_all_records():
    redis = Redis()
    committer = RedisCompensationCommitter(
        redis,
        compensation_prefix="comp",
        execution_prefix="exec",
        outbox_prefix="outbox",
    )
    event = committer.commit_success(
        compensation=Compensation(),
        execution=Execution(),
        result_payload={"ok": True},
        now=100,
    )

    assert json.loads(redis.values["comp:record:c1"])["status"] == "COMPLETED"
    assert json.loads(redis.values["exec:c1"])["status"] == "COMPLETED"
    assert event.payload == {"ok": True}
    assert "c1" in redis.sets["comp:status:COMPLETED"]
