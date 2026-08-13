from dataclasses import replace

from apps.api.app.transparency_log import (
    RedisTransparencyLogRepository,
    TransparencyCheckpoint,
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


class Empty:
    repository = None


def service():
    return TransparencyLogService(
        repository=RedisTransparencyLogRepository(
            Redis(),
            prefix="transparency",
        ),
        change_management_service=Empty(),
        compliance_attestation_service=Empty(),
    )


def test_checkpoint_chain_verification():
    item = service()
    repo = item.repository

    first = TransparencyCheckpoint(
        checkpoint_id="cp1",
        tenant_id="t1",
        tree_size=1,
        root_hash="a" * 64,
        previous_checkpoint_hash=None,
        checkpoint_hash="",
        generated_at=100,
    )
    canonical = {
        "checkpoint_id": first.checkpoint_id,
        "tenant_id": first.tenant_id,
        "tree_size": first.tree_size,
        "root_hash": first.root_hash,
        "previous_checkpoint_hash": None,
        "generated_at": first.generated_at,
    }
    import hashlib, json
    first = replace(
        first,
        checkpoint_hash=hashlib.sha256(
            json.dumps(
                canonical,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
    )
    repo.save_checkpoint(first)

    result = item.verify_checkpoint_chain(
        tenant_id="t1"
    )

    assert result["valid"] is True
    assert result["checkpoint_count"] == 1
