from dataclasses import dataclass

from apps.api.app.transparency_log import (
    RedisTransparencyLogRepository,
    TransparencyCheckpoint,
    TransparencyEntry,
    TransparencyLogService,
)
from apps.api.app.transparency_witness import (
    RedisTransparencyWitnessRepository,
    TransparencyWitnessService,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


class Empty:
    repository = None


def build():
    redis = Redis()
    log_repo = RedisTransparencyLogRepository(
        redis,
        prefix="log",
    )
    log = TransparencyLogService(
        repository=log_repo,
        change_management_service=Empty(),
        compliance_attestation_service=Empty(),
    )
    witness = TransparencyWitnessService(
        repository=(
            RedisTransparencyWitnessRepository(
                redis,
                prefix="witness",
            )
        ),
        transparency_log_service=log,
    )
    return log, witness


def test_witness_quorum():
    log, service = build()
    checkpoint = TransparencyCheckpoint(
        checkpoint_id="cp1",
        tenant_id="t1",
        tree_size=1,
        root_hash="a" * 64,
        previous_checkpoint_hash=None,
        checkpoint_hash="b" * 64,
        generated_at=100,
    )
    log.repository.save_checkpoint(checkpoint)

    for witness_id in ("w1", "w2"):
        service.register_witness(
            witness_id=witness_id,
            tenant_id="t1",
            key_id=f"k-{witness_id}",
            shared_secret=(
                "secret-value-for-" + witness_id
            ),
            now=101,
        )
        service.sign_checkpoint(
            signature_id=f"s-{witness_id}",
            tenant_id="t1",
            checkpoint_id="cp1",
            witness_id=witness_id,
            now=102,
        )

    result = service.verify_quorum(
        tenant_id="t1",
        checkpoint_id="cp1",
        required_witnesses=2,
        now=103,
    )

    assert result.quorum_met is True
    assert result.valid_witnesses == ("w1", "w2")
    assert result.invalid_witnesses == ()
