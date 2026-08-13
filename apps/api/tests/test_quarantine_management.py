import json
import pytest

from apps.api.app.distributed_lease import StaleFencingToken
from apps.api.app.maintenance_progress import MaintenanceProgress
from apps.api.app.quarantine_management import RedisQuarantineManager

class FakeRedis:
    def __init__(self):
        self.values = {
            "journal:quarantine:c1": json.dumps({
                "claim_id": "c1",
                "index_key": "index-a",
                "phase": "subject",
            }),
            "fence": 5,
        }

    def get(self, key):
        return self.values.get(key)

    def eval(self, script, number_of_keys, *args):
        quarantine_key, audit_key, fence_key = args[:3]
        token = int(args[3])
        payload = args[4]
        current = int(self.values.get(fence_key, 0))
        if token < current:
            return [-1, current]
        if quarantine_key not in self.values:
            return [0, "missing"]
        self.values[fence_key] = token
        self.values.pop(quarantine_key, None)
        self.values[audit_key] = payload
        return [1, token]

    def scan(self, cursor, match, count):
        return 0, [k for k in self.values if ":audit:" in k]

class ProgressRepo:
    def __init__(self):
        self.state = MaintenanceProgress(
            phase="family",
            cursor=12,
            pending_keys=(),
            fencing_token=5,
            updated_at=0,
            completed_cycles=2,
            processed_indexes=20,
        )

    def load(self):
        return self.state

    def save(self, value):
        self.state = value

def test_release_requeues_index_and_writes_history():
    redis = FakeRedis()
    manager = RedisQuarantineManager(
        redis,
        journal_prefix="journal",
        fence_key="fence",
    )
    action = manager.release(
        claim_id="c1",
        operator="admin",
        note="Sorun düzeltildi",
        fencing_token=6,
        now=100,
    )
    progress_repo = ProgressRepo()
    progress = manager.requeue(
        action=action,
        progress_repository=progress_repo,
    )

    assert action.index_key == "index-a"
    assert progress.phase == "subject"
    assert progress.pending_keys == ("index-a",)
    assert len(manager.history("c1")) == 1

def test_stale_release_rejected():
    redis = FakeRedis()
    manager = RedisQuarantineManager(
        redis,
        journal_prefix="journal",
        fence_key="fence",
    )
    with pytest.raises(StaleFencingToken):
        manager.release(
            claim_id="c1",
            operator="ops",
            note="retry",
            fencing_token=4,
            now=100,
        )
