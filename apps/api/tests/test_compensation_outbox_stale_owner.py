import json
import pytest
from dataclasses import dataclass

from apps.api.app.compensation_execution import CompensationOwnershipLost
from apps.api.app.compensation_outbox import RedisCompensationCommitter

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
    owner_token: str = "stale"
    status: str = "IN_PROGRESS"
    claimed_at: int = 1
    heartbeat_at: int = 1
    lease_expires_at: int = 61
    attempts: int = 1

class Redis:
    def __init__(self):
        self.values = {
            "exec:c1": json.dumps({
                **Execution().__dict__,
                "owner_token": "fresh",
            })
        }

    def eval(self, script, number_of_keys, *args):
        return [2, self.values["exec:c1"]]

def test_stale_owner_cannot_atomically_commit():
    committer = RedisCompensationCommitter(
        Redis(),
        compensation_prefix="comp",
        execution_prefix="exec",
        outbox_prefix="outbox",
    )
    with pytest.raises(CompensationOwnershipLost):
        committer.commit_success(
            compensation=Compensation(),
            execution=Execution(),
            result_payload={},
            now=100,
        )
