from __future__ import annotations
from dataclasses import dataclass
import time

@dataclass(frozen=True)
class QuarantineClosureResult:
    claim_id: str
    status: str
    verified: bool
    released: bool
    reason: str
    operator: str
    created_at: int

class VerifiedQuarantineClosureService:
    def __init__(
        self,
        *,
        verification_service,
        quarantine_manager,
        progress_repository,
    ):
        self.verification_service = verification_service
        self.quarantine_manager = quarantine_manager
        self.progress_repository = progress_repository

    def close(
        self,
        *,
        claim_id: str,
        operator: str,
        note: str,
        fencing_token: int,
        now: int | None = None,
    ) -> QuarantineClosureResult:
        current = int(now if now is not None else time.time())
        evidence = self.verification_service.retry_and_verify(
            claim_id=claim_id,
            operator=operator,
            fencing_token=fencing_token,
            now=current,
        )
        if not evidence.verified:
            return QuarantineClosureResult(
                claim_id=claim_id,
                status="HELD",
                verified=False,
                released=False,
                reason=evidence.reason,
                operator=operator,
                created_at=current,
            )

        try:
            action = self.quarantine_manager.release(
                claim_id=claim_id,
                operator=operator,
                note=note,
                fencing_token=fencing_token,
                now=current,
            )
            self.quarantine_manager.requeue(
                action=action,
                progress_repository=self.progress_repository,
            )
            released = True
        except KeyError:
            # Idempotent closure: already released is considered complete.
            released = False

        return QuarantineClosureResult(
            claim_id=claim_id,
            status="CLOSED",
            verified=True,
            released=released,
            reason=evidence.reason,
            operator=operator,
            created_at=current,
        )
