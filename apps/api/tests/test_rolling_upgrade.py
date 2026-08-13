import json
import pytest
from apps.api.app.rolling_upgrade import (
    IncompatibleRelease,
    RedisRollingUpgradeRepository,
    RollingUpgradeCoordinator,
    UpgradeConflict,
)

class Redis:
    def __init__(self):
        self.values = {}
    def get(self, key):
        return self.values.get(key)
    def eval(self, script, number_of_keys, *args):
        key = args[0]
        expected = int(args[1])
        payload = args[2]
        existing = self.values.get(key)
        if existing is not None:
            if int(json.loads(existing)['current_generation']) != expected:
                return [0, existing]
        elif expected != 0:
            return [0, 'missing']
        self.values[key] = payload
        return [1, payload]

def make():
    return RollingUpgradeCoordinator(
        repository=RedisRollingUpgradeRepository(
            Redis(),
            prefix='upgrade',
        )
    )

def test_rollout_advances_to_full():
    service = make()
    state = service.start(
        rollout_id='r1',
        source_version='10.45.0',
        target_version='10.46.0',
        schema_compatible=True,
        now=1,
    )
    assert state.stage == 'VALIDATING'
    for _ in range(4):
        state = service.advance('r1', health_ok=True, now=2)
    assert state.status == 'COMPLETED'
    assert state.traffic_percent == 100

def test_failed_health_gate_rolls_back():
    service = make()
    service.start(
        rollout_id='r1',
        source_version='10.45.0',
        target_version='10.46.0',
        schema_compatible=True,
        now=1,
    )
    state = service.advance('r1', health_ok=False, now=2)
    assert state.status == 'ROLLED_BACK'
    assert state.traffic_percent == 0

def test_incompatible_schema_is_rejected():
    with pytest.raises(IncompatibleRelease):
        make().start(
            rollout_id='r1',
            source_version='10.45.0',
            target_version='10.46.0',
            schema_compatible=False,
            now=1,
        )

def test_generation_conflict_is_rejected():
    redis = Redis()
    repo = RedisRollingUpgradeRepository(redis, prefix='upgrade')
    service = RollingUpgradeCoordinator(repository=repo)
    state = service.start(
        rollout_id='r1',
        source_version='10.45.0',
        target_version='10.46.0',
        schema_compatible=True,
        now=1,
    )
    stale = state.__class__(
        **{
            **state.__dict__,
            'expected_generation': 0,
            'current_generation': 2,
        }
    )
    with pytest.raises(UpgradeConflict):
        repo.save(stale)
