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
        return self.state

class Redis:
    def __init__(self):
        self.scan_calls = 0
        self.cleaned = []

    def scan(self, cursor, match, count):
        self.scan_calls += 1
        if self.scan_calls == 1:
            return 22, [
                "index-a",
                "index-b",
                "index-c",
            ]
        return 0, []

    def smembers(self, key):
        self.cleaned.append(key)
        return set()

    def ttl(self, key):
        return -2

    def delete(self, key):
        return 1

def test_partial_scan_batch_is_not_skipped():
    redis = Redis()
    progress = Progress()

    first = RedisSessionIndexMaintainer(
        redis,
        progress_repository=progress,
        max_indexes_per_run=1,
        time_budget_seconds=100,
    ).run_once()

    assert first.batch_limit_reached is True
    assert progress.state.pending_keys == (
        "index-b",
        "index-c",
    )
    assert progress.state.cursor == 22

    second = RedisSessionIndexMaintainer(
        redis,
        progress_repository=progress,
        max_indexes_per_run=10,
        time_budget_seconds=100,
    ).run_once()

    assert redis.cleaned[:3] == [
        "index-a",
        "index-b",
        "index-c",
    ]
    assert second.processed_indexes >= 3
