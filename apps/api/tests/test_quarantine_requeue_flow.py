from apps.api.app.maintenance_progress import MaintenanceProgress
from apps.api.app.quarantine_management import (
    QuarantineAction,
    RedisQuarantineManager,
)

class ProgressRepo:
    def __init__(self):
        self.state = MaintenanceProgress(
            phase="family",
            cursor=44,
            pending_keys=("other",),
            fencing_token=8,
            updated_at=0,
            completed_cycles=3,
            processed_indexes=120,
        )

    def load(self):
        return self.state

    def save(self, value):
        self.state = value

def test_requeue_preserves_existing_progress_and_prevents_duplicate():
    manager = object.__new__(RedisQuarantineManager)
    repo = ProgressRepo()
    action = QuarantineAction(
        claim_id="c1",
        index_key="bad-index",
        phase="subject",
        action="RELEASE",
        operator="admin",
        note="fixed",
        fencing_token=9,
        created_at=10,
    )

    first = manager.requeue(action=action, progress_repository=repo)
    second = manager.requeue(action=action, progress_repository=repo)

    assert first.pending_keys == ("bad-index", "other")
    assert second.pending_keys == ("bad-index", "other")
    assert second.processed_indexes == 120
