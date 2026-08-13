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

    def advance(self, **kwargs):
        self.state = MaintenanceProgress(
            updated_at=0,
            **kwargs,
        )

class Journal:
    def __init__(self):
        self.completed = set()
        self.claimed = set()

    def is_completed(self, claim_id):
        return claim_id in self.completed

    def claim(self, **kwargs):
        claim_id = kwargs["claim_id"]
        if claim_id in self.claimed:
            return None
        self.claimed.add(claim_id)

        class Claim:
            pass

        claim = Claim()
        for key, value in kwargs.items():
            setattr(claim, key, value)
        return claim

    def complete(self, *, claim, removed, repaired):
        self.completed.add(claim.claim_id)

class Redis:
    def __init__(self):
        self.clean_calls = 0

    def scan(self, cursor, match, count):
        return 0, ["index-a"]

    def smembers(self, key):
        self.clean_calls += 1
        return set()

    def ttl(self, key):
        return -2

    def delete(self, key):
        return 1

def test_completed_journal_entry_skips_duplicate_mutation():
    redis = Redis()
    progress = Progress()
    journal = Journal()

    first = RedisSessionIndexMaintainer(
        redis,
        progress_repository=progress,
        journal=journal,
        max_indexes_per_run=1,
        time_budget_seconds=100,
    )
    first.run_once()
    assert redis.clean_calls == 1

    # Simulate progress rollback after mutation completed.
    progress.state = MaintenanceProgress(
        phase="subject",
        cursor=0,
        pending_keys=("index-a",),
        fencing_token=0,
        updated_at=0,
        completed_cycles=0,
        processed_indexes=0,
    )

    second = RedisSessionIndexMaintainer(
        redis,
        progress_repository=progress,
        journal=journal,
        max_indexes_per_run=1,
        time_budget_seconds=100,
    )
    second.run_once()

    assert redis.clean_calls == 1
    assert progress.state.pending_keys == ()
