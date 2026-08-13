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

class Claim:
    def __init__(self, claim_id, attempts):
        self.claim_id = claim_id
        self.owner_id = "owner"
        self.index_key = "bad-index"
        self.phase = "subject"
        self.fencing_token = 0
        self.attempts = attempts

class Journal:
    def __init__(self):
        self.attempts = 0
        self.quarantined = set()

    def is_completed(self, claim_id):
        return False

    def is_quarantined(self, claim_id):
        return claim_id in self.quarantined

    def claim(self, **kwargs):
        self.attempts += 1
        return Claim(
            kwargs["claim_id"],
            self.attempts,
        )

    def should_quarantine(self, claim):
        return claim.attempts >= 3

    def quarantine(self, *, claim, error):
        self.quarantined.add(claim.claim_id)

    def complete(self, **kwargs):
        pass

class Redis:
    def scan(self, cursor, match, count):
        if "subject" in match:
            return 0, ["bad-index"]
        return 0, []

    def smembers(self, key):
        raise RuntimeError("corrupt set")

def test_poison_index_is_quarantined_after_max_attempts():
    progress = Progress()
    journal = Journal()
    redis = Redis()

    for _ in range(3):
        RedisSessionIndexMaintainer(
            redis,
            progress_repository=progress,
            journal=journal,
            max_indexes_per_run=1,
            time_budget_seconds=100,
        ).run_once()

    report = RedisSessionIndexMaintainer(
        redis,
        progress_repository=progress,
        journal=journal,
        max_indexes_per_run=1,
        time_budget_seconds=100,
    ).run_once()

    assert len(journal.quarantined) == 1
    assert progress.state.pending_keys == ()
    assert report.quarantined_indexes in (0, 1)
