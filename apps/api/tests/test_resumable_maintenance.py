from apps.api.app.maintenance_progress import (
    MaintenanceProgress,
)
from apps.api.app.session_maintenance import (
    RedisSessionIndexMaintainer,
)

class Progress:
    def __init__(self):
        self.state = MaintenanceProgress(
            phase="subject",
            cursor=0,
            pending_keys=(),
            fencing_token=0,
            updated_at=0,
            completed_cycles=0,
            processed_indexes=0,
        )

    def load(self):
        return self.state

    def advance(
        self,
        *,
        phase,
        cursor,
        pending_keys,
        fencing_token,
        completed_cycles,
        processed_indexes,
    ):
        self.state = MaintenanceProgress(
            phase=phase,
            cursor=cursor,
            pending_keys=tuple(pending_keys),
            fencing_token=fencing_token,
            updated_at=0,
            completed_cycles=completed_cycles,
            processed_indexes=processed_indexes,
        )

class FakeRedis:
    def __init__(self):
        self.calls = []

    def scan(self, cursor, match, count):
        self.calls.append((cursor, match))
        if "subject" in match:
            if cursor == 0:
                return 10, ["subject-1"]
            return 0, ["subject-2"]
        return 0, ["family-1"]

    def smembers(self, key):
        return set()

    def ttl(self, key):
        return -2

    def delete(self, key):
        return 1

def test_batch_limit_resumes_from_saved_cursor():
    redis = FakeRedis()
    progress = Progress()

    first = RedisSessionIndexMaintainer(
        redis,
        progress_repository=progress,
        max_indexes_per_run=1,
        time_budget_seconds=100,
    ).run_once()

    assert first.batch_limit_reached is True
    assert first.next_cursor == 10

    second = RedisSessionIndexMaintainer(
        redis,
        progress_repository=progress,
        max_indexes_per_run=10,
        time_budget_seconds=100,
    ).run_once()

    assert any(
        call[0] == 10
        for call in redis.calls
    )
    assert second.processed_indexes >= 2
