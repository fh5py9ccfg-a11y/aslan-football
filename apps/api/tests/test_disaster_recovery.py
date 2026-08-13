import json
import pytest

from apps.api.app.disaster_recovery import (
    PromotionRejected,
    RedisDisasterRecoveryRepository,
    SplitBrainRisk,
)

class Redis:
    def __init__(self):
        self.values = {}

    def set(self, key, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def eval(self, script, number_of_keys, *args):
        topology_key, checkpoint_key = args[:2]
        expected_epoch = int(args[2])
        payload = args[5]
        existing = self.values.get(topology_key)
        if existing:
            topology = json.loads(existing)
            if int(topology["epoch"]) != expected_epoch:
                return [-1, topology["epoch"]]
            if topology["primary_region"] == args[3]:
                return [0, existing]
        self.values[topology_key] = payload
        self.values[checkpoint_key] = payload
        return [1, payload]

def test_promotion_requires_fresh_checkpoint():
    redis = Redis()
    repo = RedisDisasterRecoveryRepository(
        redis,
        prefix="dr",
        max_rpo_seconds=30,
    )
    repo.save_checkpoint(
        region="eu-west",
        role="STANDBY",
        epoch=0,
        replication_cursor=100,
        source_timestamp=1000,
        applied_timestamp=990,
        now=1000,
    )
    result = repo.promote(
        region="eu-west",
        expected_epoch=0,
        now=1001,
    )
    assert result.status == "PROMOTED"
    assert result.new_epoch == 1

def test_stale_epoch_rejected():
    redis = Redis()
    repo = RedisDisasterRecoveryRepository(
        redis,
        prefix="dr",
    )
    repo.save_checkpoint(
        region="eu-west",
        role="STANDBY",
        epoch=0,
        replication_cursor=1,
        source_timestamp=100,
        applied_timestamp=100,
        now=100,
    )
    repo.promote(
        region="eu-west",
        expected_epoch=0,
        now=101,
    )
    repo.save_checkpoint(
        region="us-east",
        role="STANDBY",
        epoch=1,
        replication_cursor=2,
        source_timestamp=101,
        applied_timestamp=101,
        now=101,
    )
    with pytest.raises(SplitBrainRisk):
        repo.promote(
            region="us-east",
            expected_epoch=0,
            now=102,
        )

def test_rpo_limit_blocks_promotion():
    repo = RedisDisasterRecoveryRepository(
        Redis(),
        prefix="dr",
        max_rpo_seconds=5,
    )
    repo.save_checkpoint(
        region="eu-west",
        role="STANDBY",
        epoch=0,
        replication_cursor=1,
        source_timestamp=100,
        applied_timestamp=90,
        now=100,
    )
    with pytest.raises(PromotionRejected):
        repo.promote(
            region="eu-west",
            expected_epoch=0,
            now=101,
        )
