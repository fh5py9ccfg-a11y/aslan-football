from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json

@dataclass(frozen=True)
class IdempotentClosureResult:
    status: str
    payload: dict
    replayed: bool

class IdempotentClosureExecutor:
    def __init__(
        self,
        *,
        effect_repository,
        compensation_repository,
    ):
        self.effect_repository = effect_repository
        self.compensation_repository = compensation_repository

    def execute(
        self,
        *,
        request_id: str,
        claim_id: str,
        owner: str,
        operation,
    ) -> IdempotentClosureResult:
        key = self._key(request_id, claim_id)
        created, record = self.effect_repository.claim(
            key=key,
            operation="quarantine-close",
            owner=owner,
        )

        if not created:
            if record.status == "COMPLETED":
                return IdempotentClosureResult(
                    status="COMPLETED",
                    payload=record.result_payload or {},
                    replayed=True,
                )
            if record.status == "FAILED":
                return IdempotentClosureResult(
                    status="FAILED",
                    payload={"error": record.error},
                    replayed=True,
                )
            return IdempotentClosureResult(
                status="IN_PROGRESS",
                payload={},
                replayed=True,
            )

        try:
            result = operation()
            payload = dict(result.__dict__)
            self.effect_repository.complete(
                record=record,
                result_payload=payload,
            )
            return IdempotentClosureResult(
                status="COMPLETED",
                payload=payload,
                replayed=False,
            )
        except Exception as exc:
            self.effect_repository.fail(
                record=record,
                error=str(exc),
            )
            compensation = self.compensation_repository.create(
                request_id=request_id,
                claim_id=claim_id,
                action="RECONCILE_QUARANTINE_CLOSURE",
                reason=str(exc),
            )
            return IdempotentClosureResult(
                status="FAILED",
                payload={
                    "error": str(exc),
                    "compensation_id": compensation.compensation_id,
                },
                replayed=False,
            )

    @staticmethod
    def _key(request_id: str, claim_id: str) -> str:
        raw = f"{request_id}:{claim_id}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
