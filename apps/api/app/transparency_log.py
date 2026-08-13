from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time


@dataclass(frozen=True)
class TransparencyEntry:
    entry_id: str
    tenant_id: str
    release_id: str
    evidence_sha256: str
    attestation_signature: str
    leaf_hash: str
    sequence: int
    created_at: int


@dataclass(frozen=True)
class TransparencyCheckpoint:
    checkpoint_id: str
    tenant_id: str
    tree_size: int
    root_hash: str
    previous_checkpoint_hash: str | None
    checkpoint_hash: str
    generated_at: int


@dataclass(frozen=True)
class InclusionProof:
    entry_id: str
    tenant_id: str
    leaf_hash: str
    leaf_index: int
    tree_size: int
    root_hash: str
    audit_path: tuple[str, ...]
    generated_at: int


class TransparencyLogError(RuntimeError):
    pass


class TransparencyLogValidationError(ValueError):
    pass


class RedisTransparencyLogRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:transparency-log",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_entry(
        self,
        entry: TransparencyEntry,
    ) -> TransparencyEntry:
        self.client.setex(
            self._entry_key(entry.entry_id),
            self.ttl_seconds,
            json.dumps(
                entry.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._tenant_entry_index(entry.tenant_id),
            entry.entry_id,
        )
        return entry

    def get_entry(
        self,
        entry_id: str,
    ) -> TransparencyEntry | None:
        payload = self.client.get(
            self._entry_key(entry_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return TransparencyEntry(**json.loads(payload))

    def list_entries(
        self,
        tenant_id: str,
    ) -> tuple[TransparencyEntry, ...]:
        items = []
        for entry_id in self.client.smembers(
            self._tenant_entry_index(tenant_id)
        ):
            if isinstance(entry_id, bytes):
                entry_id = entry_id.decode("utf-8")
            entry = self.get_entry(str(entry_id))
            if entry is not None:
                items.append(entry)
        items.sort(key=lambda item: item.sequence)
        return tuple(items)

    def save_checkpoint(
        self,
        checkpoint: TransparencyCheckpoint,
    ) -> TransparencyCheckpoint:
        self.client.setex(
            self._checkpoint_key(
                checkpoint.checkpoint_id
            ),
            self.ttl_seconds,
            json.dumps(
                checkpoint.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._tenant_checkpoint_index(
                checkpoint.tenant_id
            ),
            checkpoint.checkpoint_id,
        )
        return checkpoint

    def list_checkpoints(
        self,
        tenant_id: str,
    ) -> tuple[TransparencyCheckpoint, ...]:
        items = []
        for checkpoint_id in self.client.smembers(
            self._tenant_checkpoint_index(
                tenant_id
            )
        ):
            if isinstance(checkpoint_id, bytes):
                checkpoint_id = checkpoint_id.decode(
                    "utf-8"
                )
            payload = self.client.get(
                self._checkpoint_key(
                    str(checkpoint_id)
                )
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                TransparencyCheckpoint(
                    **json.loads(payload)
                )
            )
        items.sort(
            key=lambda item: item.generated_at
        )
        return tuple(items)

    def latest_checkpoint(
        self,
        tenant_id: str,
    ) -> TransparencyCheckpoint | None:
        items = self.list_checkpoints(tenant_id)
        return items[-1] if items else None

    def _entry_key(self, entry_id: str) -> str:
        return f"{self.prefix}:entry:{entry_id}"

    def _tenant_entry_index(
        self,
        tenant_id: str,
    ) -> str:
        return f"{self.prefix}:entries:{tenant_id}"

    def _checkpoint_key(
        self,
        checkpoint_id: str,
    ) -> str:
        return (
            f"{self.prefix}:checkpoint:"
            f"{checkpoint_id}"
        )

    def _tenant_checkpoint_index(
        self,
        tenant_id: str,
    ) -> str:
        return (
            f"{self.prefix}:checkpoints:"
            f"{tenant_id}"
        )


class TransparencyLogService:
    def __init__(
        self,
        *,
        repository,
        change_management_service,
        compliance_attestation_service,
    ):
        self.repository = repository
        self.change_management_service = (
            change_management_service
        )
        self.compliance_attestation_service = (
            compliance_attestation_service
        )

    def append(
        self,
        *,
        entry_id: str,
        tenant_id: str,
        change_id: str,
        now: int | None = None,
    ) -> TransparencyEntry:
        evidence = (
            self.change_management_service
            .repository.get_evidence(change_id)
        )
        if evidence is None:
            raise KeyError(
                "Release evidence bulunamadı"
            )

        attestation = (
            self.compliance_attestation_service
            .repository.get_attestation(change_id)
        )
        if attestation is None:
            raise KeyError(
                "Compliance attestation bulunamadı"
            )

        verification = (
            self.compliance_attestation_service
            .verify(change_id=change_id)
        )
        if not verification["valid"]:
            raise TransparencyLogError(
                "Geçersiz attestation transparency log'a eklenemez"
            )

        existing = self.repository.get_entry(entry_id)
        if existing is not None:
            return existing

        entries = self.repository.list_entries(
            tenant_id
        )
        sequence = len(entries) + 1
        canonical = {
            "entry_id": entry_id,
            "tenant_id": tenant_id,
            "release_id": evidence.release_id,
            "evidence_sha256": (
                evidence.evidence_sha256
            ),
            "attestation_signature": (
                attestation.signature
            ),
            "sequence": sequence,
        }
        leaf_hash = hashlib.sha256(
            json.dumps(
                canonical,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        entry = TransparencyEntry(
            **canonical,
            leaf_hash=leaf_hash,
            created_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_entry(entry)

    def create_checkpoint(
        self,
        *,
        checkpoint_id: str,
        tenant_id: str,
        now: int | None = None,
    ) -> TransparencyCheckpoint:
        entries = self.repository.list_entries(
            tenant_id
        )
        if not entries:
            raise TransparencyLogError(
                "Checkpoint için en az bir entry gereklidir"
            )

        root_hash = self._merkle_root(
            tuple(item.leaf_hash for item in entries)
        )
        previous = (
            self.repository.latest_checkpoint(
                tenant_id
            )
        )
        generated_at = int(
            now if now is not None
            else time.time()
        )
        canonical = {
            "checkpoint_id": checkpoint_id,
            "tenant_id": tenant_id,
            "tree_size": len(entries),
            "root_hash": root_hash,
            "previous_checkpoint_hash": (
                previous.checkpoint_hash
                if previous is not None
                else None
            ),
            "generated_at": generated_at,
        }
        checkpoint_hash = hashlib.sha256(
            json.dumps(
                canonical,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        checkpoint = TransparencyCheckpoint(
            **canonical,
            checkpoint_hash=checkpoint_hash,
        )
        return self.repository.save_checkpoint(
            checkpoint
        )

    def inclusion_proof(
        self,
        *,
        tenant_id: str,
        entry_id: str,
        now: int | None = None,
    ) -> InclusionProof:
        entries = self.repository.list_entries(
            tenant_id
        )
        index = next(
            (
                idx
                for idx, item in enumerate(entries)
                if item.entry_id == entry_id
            ),
            None,
        )
        if index is None:
            raise KeyError(
                "Transparency entry bulunamadı"
            )

        hashes = [item.leaf_hash for item in entries]
        audit_path = []
        cursor = index
        level = hashes[:]

        while len(level) > 1:
            if len(level) % 2 == 1:
                level.append(level[-1])

            sibling = (
                cursor - 1
                if cursor % 2 == 1
                else cursor + 1
            )
            audit_path.append(level[sibling])

            next_level = []
            for offset in range(0, len(level), 2):
                next_level.append(
                    self._parent_hash(
                        level[offset],
                        level[offset + 1],
                    )
                )
            cursor //= 2
            level = next_level

        root_hash = level[0]
        return InclusionProof(
            entry_id=entry_id,
            tenant_id=tenant_id,
            leaf_hash=entries[index].leaf_hash,
            leaf_index=index,
            tree_size=len(entries),
            root_hash=root_hash,
            audit_path=tuple(audit_path),
            generated_at=int(
                now if now is not None
                else time.time()
            ),
        )

    def verify_inclusion(
        self,
        *,
        proof: InclusionProof,
    ) -> bool:
        current = proof.leaf_hash
        index = proof.leaf_index

        for sibling in proof.audit_path:
            if index % 2 == 0:
                current = self._parent_hash(
                    current,
                    sibling,
                )
            else:
                current = self._parent_hash(
                    sibling,
                    current,
                )
            index //= 2

        return current == proof.root_hash

    def verify_checkpoint_chain(
        self,
        *,
        tenant_id: str,
    ) -> dict:
        checkpoints = (
            self.repository.list_checkpoints(
                tenant_id
            )
        )
        previous_hash = None

        for checkpoint in checkpoints:
            canonical = {
                "checkpoint_id": (
                    checkpoint.checkpoint_id
                ),
                "tenant_id": checkpoint.tenant_id,
                "tree_size": checkpoint.tree_size,
                "root_hash": checkpoint.root_hash,
                "previous_checkpoint_hash": (
                    checkpoint.previous_checkpoint_hash
                ),
                "generated_at": (
                    checkpoint.generated_at
                ),
            }
            expected = hashlib.sha256(
                json.dumps(
                    canonical,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()

            if expected != checkpoint.checkpoint_hash:
                return {
                    "valid": False,
                    "broken_checkpoint_id": (
                        checkpoint.checkpoint_id
                    ),
                    "reason": (
                        "Checkpoint hash mismatch"
                    ),
                }
            if (
                checkpoint.previous_checkpoint_hash
                != previous_hash
            ):
                return {
                    "valid": False,
                    "broken_checkpoint_id": (
                        checkpoint.checkpoint_id
                    ),
                    "reason": (
                        "Checkpoint chain mismatch"
                    ),
                }
            previous_hash = (
                checkpoint.checkpoint_hash
            )

        return {
            "valid": True,
            "checkpoint_count": len(checkpoints),
            "latest_checkpoint_hash": (
                previous_hash
            ),
        }

    @staticmethod
    def _parent_hash(
        left: str,
        right: str,
    ) -> str:
        return hashlib.sha256(
            f"{left}{right}".encode("utf-8")
        ).hexdigest()

    @classmethod
    def _merkle_root(
        cls,
        leaves: tuple[str, ...],
    ) -> str:
        level = list(leaves)
        if not level:
            raise TransparencyLogValidationError(
                "Merkle tree boş olamaz"
            )

        while len(level) > 1:
            if len(level) % 2 == 1:
                level.append(level[-1])
            level = [
                cls._parent_hash(
                    level[index],
                    level[index + 1],
                )
                for index in range(
                    0,
                    len(level),
                    2,
                )
            ]
        return level[0]
