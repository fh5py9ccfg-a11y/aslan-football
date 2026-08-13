import json
import pytest

from apps.api.app.distributed_lease import (
    StaleFencingToken,
)
from apps.api.app.maintenance_progress import (
    MaintenanceProgress,
    RedisMaintenanceProgressRepository,
)

class FakeRedis:
    def __init__(self):
        self.value = None

    def get(self, key):
        return self.value

    def eval(
        self,
        script,
        number_of_keys,
        key,
        token,
        payload,
    ):
        if self.value is not None:
            current = json.loads(self.value)
            if int(token) < int(
                current["fencing_token"]
            ):
                return [-1, current["fencing_token"]]
        self.value = payload
        return [1, token]

def test_progress_save_load_and_stale_rejection():
    redis = FakeRedis()
    repository = RedisMaintenanceProgressRepository(
        redis
    )

    saved = repository.advance(
        phase="family",
        cursor=42,
        pending_keys=("key-a", "key-b"),
        fencing_token=5,
        completed_cycles=3,
        processed_indexes=9,
    )
    loaded = repository.load()

    assert loaded.phase == "family"
    assert loaded.cursor == 42
    assert loaded.completed_cycles == 3
    assert loaded.pending_keys == ("key-a", "key-b")
    assert loaded.processed_indexes == 9

    with pytest.raises(StaleFencingToken):
        repository.save(
            MaintenanceProgress(
                phase="subject",
                cursor=0,
                pending_keys=(),
                fencing_token=4,
                updated_at=0,
                completed_cycles=4,
                processed_indexes=10,
            )
        )
