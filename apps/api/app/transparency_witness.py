from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import time


@dataclass(frozen=True)
class WitnessRegistration:
    witness_id: str
    tenant_id: str
    key_id: str
    shared_secret: str
    enabled: bool
    created_at: int


@dataclass(frozen=True)
class CheckpointWitnessSignature:
    signature_id: str
    checkpoint_id: str
    tenant_id: str
    witness_id: str
    key_id: str
    checkpoint_hash: str
    signature: str
    signed_at: int


@dataclass(frozen=True)
class CheckpointQuorumResult:
    checkpoint_id: str
    tenant_id: str
    required_witnesses: int
    valid_witnesses: tuple[str, ...]
    invalid_witnesses: tuple[str, ...]
    quorum_met: bool
    evaluated_at: int


@dataclass(frozen=True)
class CheckpointConsistencyProof:
    tenant_id: str
    from_checkpoint_id: str
    to_checkpoint_id: str
    from_tree_size: int
    to_tree_size: int
    from_root_hash: str
    to_root_hash: str
    appended_leaf_hashes: tuple[str, ...]
    proof_hash: str
    generated_at: int


class TransparencyWitnessError(RuntimeError):
    pass


class TransparencyWitnessValidationError(ValueError):
    pass


class RedisTransparencyWitnessRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:transparency-witness",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_witness(
        self,
        witness: WitnessRegistration,
    ) -> WitnessRegistration:
        self.client.setex(
            self._witness_key(
                witness.tenant_id,
                witness.witness_id,
            ),
            self.ttl_seconds,
            json.dumps(
                witness.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._tenant_witness_index(
                witness.tenant_id
            ),
            witness.witness_id,
        )
        return witness

    def get_witness(
        self,
        *,
        tenant_id: str,
        witness_id: str,
    ) -> WitnessRegistration | None:
        payload = self.client.get(
            self._witness_key(
                tenant_id,
                witness_id,
            )
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return WitnessRegistration(
            **json.loads(payload)
        )

    def list_witnesses(
        self,
        tenant_id: str,
    ) -> tuple[WitnessRegistration, ...]:
        items = []
        for witness_id in self.client.smembers(
            self._tenant_witness_index(tenant_id)
        ):
            if isinstance(witness_id, bytes):
                witness_id = witness_id.decode("utf-8")
            item = self.get_witness(
                tenant_id=tenant_id,
                witness_id=str(witness_id),
            )
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.witness_id)
        return tuple(items)

    def save_signature(
        self,
        signature: CheckpointWitnessSignature,
    ) -> CheckpointWitnessSignature:
        self.client.setex(
            self._signature_key(
                signature.signature_id
            ),
            self.ttl_seconds,
            json.dumps(
                signature.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._checkpoint_signature_index(
                signature.checkpoint_id
            ),
            signature.signature_id,
        )
        return signature

    def list_signatures(
        self,
        checkpoint_id: str,
    ) -> tuple[CheckpointWitnessSignature, ...]:
        items = []
        for signature_id in self.client.smembers(
            self._checkpoint_signature_index(
                checkpoint_id
            )
        ):
            if isinstance(signature_id, bytes):
                signature_id = signature_id.decode(
                    "utf-8"
                )
            payload = self.client.get(
                self._signature_key(
                    str(signature_id)
                )
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                CheckpointWitnessSignature(
                    **json.loads(payload)
                )
            )
        items.sort(
            key=lambda item: (
                item.signed_at,
                item.witness_id,
            )
        )
        return tuple(items)

    def save_quorum(
        self,
        result: CheckpointQuorumResult,
    ) -> CheckpointQuorumResult:
        payload = {
            **result.__dict__,
            "valid_witnesses": list(
                result.valid_witnesses
            ),
            "invalid_witnesses": list(
                result.invalid_witnesses
            ),
        }
        self.client.setex(
            self._quorum_key(result.checkpoint_id),
            self.ttl_seconds,
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        return result

    def save_consistency_proof(
        self,
        proof: CheckpointConsistencyProof,
    ) -> CheckpointConsistencyProof:
        payload = {
            **proof.__dict__,
            "appended_leaf_hashes": list(
                proof.appended_leaf_hashes
            ),
        }
        self.client.setex(
            self._consistency_key(
                proof.from_checkpoint_id,
                proof.to_checkpoint_id,
            ),
            self.ttl_seconds,
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        return proof

    def _witness_key(
        self,
        tenant_id: str,
        witness_id: str,
    ) -> str:
        return (
            f"{self.prefix}:witness:"
            f"{tenant_id}:{witness_id}"
        )

    def _tenant_witness_index(
        self,
        tenant_id: str,
    ) -> str:
        return (
            f"{self.prefix}:witnesses:"
            f"{tenant_id}"
        )

    def _signature_key(
        self,
        signature_id: str,
    ) -> str:
        return (
            f"{self.prefix}:signature:"
            f"{signature_id}"
        )

    def _checkpoint_signature_index(
        self,
        checkpoint_id: str,
    ) -> str:
        return (
            f"{self.prefix}:signatures:"
            f"{checkpoint_id}"
        )

    def _quorum_key(
        self,
        checkpoint_id: str,
    ) -> str:
        return (
            f"{self.prefix}:quorum:"
            f"{checkpoint_id}"
        )

    def _consistency_key(
        self,
        from_checkpoint_id: str,
        to_checkpoint_id: str,
    ) -> str:
        return (
            f"{self.prefix}:consistency:"
            f"{from_checkpoint_id}:"
            f"{to_checkpoint_id}"
        )


class TransparencyWitnessService:
    def __init__(
        self,
        *,
        repository,
        transparency_log_service,
    ):
        self.repository = repository
        self.transparency_log_service = (
            transparency_log_service
        )

    def register_witness(
        self,
        *,
        witness_id: str,
        tenant_id: str,
        key_id: str,
        shared_secret: str,
        now: int | None = None,
    ) -> WitnessRegistration:
        if len(shared_secret) < 16:
            raise TransparencyWitnessValidationError(
                "Witness secret en az 16 karakter olmalıdır"
            )
        item = WitnessRegistration(
            witness_id=witness_id,
            tenant_id=tenant_id,
            key_id=key_id,
            shared_secret=shared_secret,
            enabled=True,
            created_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_witness(item)

    def sign_checkpoint(
        self,
        *,
        signature_id: str,
        tenant_id: str,
        checkpoint_id: str,
        witness_id: str,
        now: int | None = None,
    ) -> CheckpointWitnessSignature:
        checkpoint = self._checkpoint(
            tenant_id=tenant_id,
            checkpoint_id=checkpoint_id,
        )
        witness = self.repository.get_witness(
            tenant_id=tenant_id,
            witness_id=witness_id,
        )
        if witness is None:
            raise KeyError("Witness bulunamadı")
        if not witness.enabled:
            raise TransparencyWitnessError(
                "Witness devre dışı"
            )

        signature = hmac.new(
            witness.shared_secret.encode("utf-8"),
            checkpoint.checkpoint_hash.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        item = CheckpointWitnessSignature(
            signature_id=signature_id,
            checkpoint_id=checkpoint_id,
            tenant_id=tenant_id,
            witness_id=witness_id,
            key_id=witness.key_id,
            checkpoint_hash=(
                checkpoint.checkpoint_hash
            ),
            signature=signature,
            signed_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_signature(item)

    def verify_quorum(
        self,
        *,
        tenant_id: str,
        checkpoint_id: str,
        required_witnesses: int,
        now: int | None = None,
    ) -> CheckpointQuorumResult:
        if required_witnesses < 1:
            raise TransparencyWitnessValidationError(
                "Quorum en az 1 olmalıdır"
            )

        checkpoint = self._checkpoint(
            tenant_id=tenant_id,
            checkpoint_id=checkpoint_id,
        )
        valid = []
        invalid = []

        for item in self.repository.list_signatures(
            checkpoint_id
        ):
            witness = self.repository.get_witness(
                tenant_id=tenant_id,
                witness_id=item.witness_id,
            )
            if (
                witness is None
                or not witness.enabled
                or item.checkpoint_hash
                != checkpoint.checkpoint_hash
            ):
                invalid.append(item.witness_id)
                continue

            expected = hmac.new(
                witness.shared_secret.encode("utf-8"),
                checkpoint.checkpoint_hash.encode(
                    "utf-8"
                ),
                hashlib.sha256,
            ).hexdigest()

            if hmac.compare_digest(
                expected,
                item.signature,
            ):
                valid.append(item.witness_id)
            else:
                invalid.append(item.witness_id)

        result = CheckpointQuorumResult(
            checkpoint_id=checkpoint_id,
            tenant_id=tenant_id,
            required_witnesses=required_witnesses,
            valid_witnesses=tuple(sorted(set(valid))),
            invalid_witnesses=tuple(
                sorted(set(invalid))
            ),
            quorum_met=(
                len(set(valid)) >= required_witnesses
            ),
            evaluated_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_quorum(result)

    def consistency_proof(
        self,
        *,
        tenant_id: str,
        from_checkpoint_id: str,
        to_checkpoint_id: str,
        now: int | None = None,
    ) -> CheckpointConsistencyProof:
        source = self._checkpoint(
            tenant_id=tenant_id,
            checkpoint_id=from_checkpoint_id,
        )
        target = self._checkpoint(
            tenant_id=tenant_id,
            checkpoint_id=to_checkpoint_id,
        )

        if target.tree_size < source.tree_size:
            raise TransparencyWitnessValidationError(
                "Target checkpoint source'tan eski olamaz"
            )

        entries = (
            self.transparency_log_service
            .repository.list_entries(tenant_id)
        )
        if len(entries) < target.tree_size:
            raise TransparencyWitnessError(
                "Transparency entry seti target checkpoint'i karşılamıyor"
            )

        source_root = (
            self.transparency_log_service
            ._merkle_root(
                tuple(
                    item.leaf_hash
                    for item in entries[
                        : source.tree_size
                    ]
                )
            )
        )
        target_root = (
            self.transparency_log_service
            ._merkle_root(
                tuple(
                    item.leaf_hash
                    for item in entries[
                        : target.tree_size
                    ]
                )
            )
        )

        if source_root != source.root_hash:
            raise TransparencyWitnessError(
                "Source checkpoint fork veya stale"
            )
        if target_root != target.root_hash:
            raise TransparencyWitnessError(
                "Target checkpoint fork veya stale"
            )

        appended = tuple(
            item.leaf_hash
            for item in entries[
                source.tree_size : target.tree_size
            ]
        )
        canonical = {
            "tenant_id": tenant_id,
            "from_checkpoint_id": (
                from_checkpoint_id
            ),
            "to_checkpoint_id": (
                to_checkpoint_id
            ),
            "from_tree_size": source.tree_size,
            "to_tree_size": target.tree_size,
            "from_root_hash": source.root_hash,
            "to_root_hash": target.root_hash,
            "appended_leaf_hashes": list(appended),
        }
        proof_hash = hashlib.sha256(
            json.dumps(
                canonical,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        proof = CheckpointConsistencyProof(
            tenant_id=tenant_id,
            from_checkpoint_id=from_checkpoint_id,
            to_checkpoint_id=to_checkpoint_id,
            from_tree_size=source.tree_size,
            to_tree_size=target.tree_size,
            from_root_hash=source.root_hash,
            to_root_hash=target.root_hash,
            appended_leaf_hashes=appended,
            proof_hash=proof_hash,
            generated_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_consistency_proof(
            proof
        )

    def verify_consistency(
        self,
        *,
        proof: CheckpointConsistencyProof,
    ) -> dict:
        canonical = {
            "tenant_id": proof.tenant_id,
            "from_checkpoint_id": (
                proof.from_checkpoint_id
            ),
            "to_checkpoint_id": (
                proof.to_checkpoint_id
            ),
            "from_tree_size": proof.from_tree_size,
            "to_tree_size": proof.to_tree_size,
            "from_root_hash": proof.from_root_hash,
            "to_root_hash": proof.to_root_hash,
            "appended_leaf_hashes": list(
                proof.appended_leaf_hashes
            ),
        }
        expected_proof_hash = hashlib.sha256(
            json.dumps(
                canonical,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        if not hmac.compare_digest(
            expected_proof_hash,
            proof.proof_hash,
        ):
            return {
                "valid": False,
                "reason": "Consistency proof hash mismatch",
            }

        entries = (
            self.transparency_log_service
            .repository.list_entries(
                proof.tenant_id
            )
        )
        if len(entries) < proof.to_tree_size:
            return {
                "valid": False,
                "reason": "Insufficient transparency entries",
            }

        from_root = (
            self.transparency_log_service
            ._merkle_root(
                tuple(
                    item.leaf_hash
                    for item in entries[
                        : proof.from_tree_size
                    ]
                )
            )
        )
        to_root = (
            self.transparency_log_service
            ._merkle_root(
                tuple(
                    item.leaf_hash
                    for item in entries[
                        : proof.to_tree_size
                    ]
                )
            )
        )
        appended = tuple(
            item.leaf_hash
            for item in entries[
                proof.from_tree_size :
                proof.to_tree_size
            ]
        )

        valid = (
            from_root == proof.from_root_hash
            and to_root == proof.to_root_hash
            and appended
            == proof.appended_leaf_hashes
        )
        return {
            "valid": valid,
            "reason": (
                "ok"
                if valid
                else "Checkpoint consistency mismatch"
            ),
        }

    def _checkpoint(
        self,
        *,
        tenant_id: str,
        checkpoint_id: str,
    ):
        for item in (
            self.transparency_log_service
            .repository.list_checkpoints(
                tenant_id
            )
        ):
            if item.checkpoint_id == checkpoint_id:
                return item
        raise KeyError(
            "Transparency checkpoint bulunamadı"
        )
