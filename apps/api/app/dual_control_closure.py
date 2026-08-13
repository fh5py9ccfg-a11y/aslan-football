from __future__ import annotations
from dataclasses import dataclass
import time

from .quarantine_approval import (
    ApprovalConflict,
    ApprovalExpired,
)

@dataclass(frozen=True)
class DualControlClosureResult:
    request_id: str
    claim_id: str
    approval_status: str
    closure_status: str
    approved_by: str | None
    closed: bool
    reason: str
    created_at: int

class DualControlQuarantineClosureService:
    def __init__(
        self,
        *,
        approval_repository,
        closure_service,
    ):
        self.approval_repository = approval_repository
        self.closure_service = closure_service

    def request_close(
        self,
        *,
        claim_id: str,
        requested_by: str,
        note: str,
        now: int | None = None,
    ):
        return self.approval_repository.create(
            claim_id=claim_id,
            requested_by=requested_by,
            note=note,
            now=now,
        )

    def decide_and_close(
        self,
        *,
        request_id: str,
        decided_by: str,
        approve: bool,
        decision_note: str,
        fencing_token: int,
        now: int | None = None,
    ) -> DualControlClosureResult:
        current = int(now if now is not None else time.time())
        approval = self.approval_repository.decide(
            request_id=request_id,
            decided_by=decided_by,
            approve=approve,
            decision_note=decision_note,
            now=current,
        )

        if approval.status != "APPROVED":
            return DualControlClosureResult(
                request_id=request_id,
                claim_id=approval.claim_id,
                approval_status=approval.status,
                closure_status="NOT_EXECUTED",
                approved_by=approval.decided_by,
                closed=False,
                reason=approval.decision_note or "Talep reddedildi",
                created_at=current,
            )

        closure = self.closure_service.close(
            claim_id=approval.claim_id,
            operator=decided_by,
            note=decision_note,
            fencing_token=fencing_token,
            now=current,
        )
        return DualControlClosureResult(
            request_id=request_id,
            claim_id=approval.claim_id,
            approval_status=approval.status,
            closure_status=closure.status,
            approved_by=decided_by,
            closed=closure.status == "CLOSED",
            reason=closure.reason,
            created_at=current,
        )
