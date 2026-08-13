from apps.api.app.maintenance_progress import (
    RedisMaintenanceProgressRepository,
)

class Redis:
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
        self.value = payload
        return [1, token]

def test_progress_reset():
    repository = RedisMaintenanceProgressRepository(
        Redis()
    )
    repository.advance(
        phase="family",
        cursor=99,
        pending_keys=("x",),
        fencing_token=7,
        completed_cycles=4,
        processed_indexes=120,
    )

    reset = repository.reset(
        fencing_token=8
    )

    assert reset.phase == "subject"
    assert reset.cursor == 0
    assert reset.pending_keys == ()
    assert reset.completed_cycles == 0
    assert reset.processed_indexes == 0
    assert reset.fencing_token == 8
