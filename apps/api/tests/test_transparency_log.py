from dataclasses import dataclass

from apps.api.app.transparency_log import (
    RedisTransparencyLogRepository,
    TransparencyLogService,
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


@dataclass
class Evidence:
    release_id: str
    evidence_sha256: str


@dataclass
class Attestation:
    signature: str


class ChangeRepository:
    def __init__(self):
        self.items = {
            "c1": Evidence("r1", "a" * 64),
            "c2": Evidence("r2", "b" * 64),
            "c3": Evidence("r3", "c" * 64),
        }

    def get_evidence(self, change_id):
        return self.items.get(change_id)


class ChangeService:
    repository = ChangeRepository()


class AttestationRepository:
    def get_attestation(self, change_id):
        return Attestation(
            signature=f"sig-{change_id}"
        )


class AttestationService:
    repository = AttestationRepository()

    def verify(self, *, change_id):
        return {"valid": True}


def build():
    return TransparencyLogService(
        repository=RedisTransparencyLogRepository(
            Redis(),
            prefix="transparency",
        ),
        change_management_service=ChangeService(),
        compliance_attestation_service=(
            AttestationService()
        ),
    )


def test_append_checkpoint_and_inclusion_proof():
    service = build()
    service.append(
        entry_id="e1",
        tenant_id="t1",
        change_id="c1",
        now=100,
    )
    service.append(
        entry_id="e2",
        tenant_id="t1",
        change_id="c2",
        now=101,
    )
    checkpoint = service.create_checkpoint(
        checkpoint_id="cp1",
        tenant_id="t1",
        now=102,
    )
    proof = service.inclusion_proof(
        tenant_id="t1",
        entry_id="e2",
        now=103,
    )

    assert checkpoint.tree_size == 2
    assert checkpoint.root_hash == proof.root_hash
    assert service.verify_inclusion(
        proof=proof
    ) is True


def test_odd_leaf_count_is_supported():
    service = build()
    for index, change_id in enumerate(
        ("c1", "c2", "c3"),
        start=1,
    ):
        service.append(
            entry_id=f"e{index}",
            tenant_id="t1",
            change_id=change_id,
            now=100 + index,
        )

    checkpoint = service.create_checkpoint(
        checkpoint_id="cp1",
        tenant_id="t1",
        now=110,
    )
    proof = service.inclusion_proof(
        tenant_id="t1",
        entry_id="e3",
        now=111,
    )

    assert checkpoint.tree_size == 3
    assert service.verify_inclusion(
        proof=proof
    ) is True
