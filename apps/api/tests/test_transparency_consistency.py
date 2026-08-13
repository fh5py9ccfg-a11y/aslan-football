from apps.api.app.transparency_log import (
    RedisTransparencyLogRepository,
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
    log = TransparencyLogService(
        repository=RedisTransparencyLogRepository(
            redis,
            prefix="log",
        ),
        change_management_service=Empty(),
        compliance_attestation_service=Empty(),
    )
    witness = TransparencyWitnessService(
        repository=RedisTransparencyWitnessRepository(
            redis,
            prefix="witness",
        ),
        transparency_log_service=log,
    )
    return log, witness


def add_entry(log, entry_id, sequence, leaf_hash):
    log.repository.save_entry(
        TransparencyEntry(
            entry_id=entry_id,
            tenant_id="t1",
            release_id=f"r{sequence}",
            evidence_sha256="e" * 64,
            attestation_signature="sig",
            leaf_hash=leaf_hash,
            sequence=sequence,
            created_at=100 + sequence,
        )
    )


def test_consistency_proof_between_checkpoints():
    log, witness = build()
    add_entry(log, "e1", 1, "a" * 64)
    first = log.create_checkpoint(
        checkpoint_id="cp1",
        tenant_id="t1",
        now=101,
    )

    add_entry(log, "e2", 2, "b" * 64)
    second = log.create_checkpoint(
        checkpoint_id="cp2",
        tenant_id="t1",
        now=102,
    )

    proof = witness.consistency_proof(
        tenant_id="t1",
        from_checkpoint_id="cp1",
        to_checkpoint_id="cp2",
        now=103,
    )
    result = witness.verify_consistency(
        proof=proof
    )

    assert first.tree_size == 1
    assert second.tree_size == 2
    assert len(proof.appended_leaf_hashes) == 1
    assert result["valid"] is True


def test_tampered_consistency_proof_fails():
    log, witness = build()
    add_entry(log, "e1", 1, "a" * 64)
    log.create_checkpoint(
        checkpoint_id="cp1",
        tenant_id="t1",
        now=101,
    )
    add_entry(log, "e2", 2, "b" * 64)
    log.create_checkpoint(
        checkpoint_id="cp2",
        tenant_id="t1",
        now=102,
    )

    proof = witness.consistency_proof(
        tenant_id="t1",
        from_checkpoint_id="cp1",
        to_checkpoint_id="cp2",
        now=103,
    )
    broken = type(proof)(
        **{
            **proof.__dict__,
            "proof_hash": "0" * 64,
        }
    )

    result = witness.verify_consistency(
        proof=broken
    )

    assert result["valid"] is False
