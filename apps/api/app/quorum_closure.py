from __future__ import annotations
from dataclasses import dataclass
import asyncio
import time

from .quorum_execution import (
    ExecutionOwnershipLost,
)
from .quorum_execution_guard import (
    QuorumExecutionGuard,
)

@dataclass(frozen=True)
class QuorumClosureResult:
    request_id: str
    claim_id: str
    status: str
    approvals: int
    rejections: int
    groups: tuple[str, ...]
    closed: bool
    reason: str
    created_at: int
    ownership_lost: bool = False

class QuorumQuarantineClosureService:
    def __init__(
        self,
        *,
        approval_repository,
        quorum_repository,
        closure_service,
        execution_repository,
        heartbeat_interval_seconds: float = 15.0,
    ):
        self.approval_repository = approval_repository
        self.quorum_repository = quorum_repository
        self.closure_service = closure_service
        self.execution_repository = (
            execution_repository
        )
        self.execution_guard = QuorumExecutionGuard(
            repository=execution_repository,
            heartbeat_interval_seconds=(
                heartbeat_interval_seconds
            ),
        )

    def prepare(
        self,
        *,
        request_id: str,
        required_approvals: int,
        required_groups: tuple[str, ...],
    ):
        request = self.approval_repository.get(
            request_id
        )
        if request is None:
            raise KeyError(
                "Onay talebi bulunamadı"
            )

        return self.quorum_repository.initialize(
            request_id=request_id,
            required_approvals=required_approvals,
            required_groups=required_groups,
            expires_at=request.expires_at,
        )

    def vote_and_maybe_close(
        self,
        *,
        request_id: str,
        voter: str,
        group: str,
        voter_roles: tuple[str, ...],
        approve: bool,
        note: str,
        fencing_token: int,
        now: int | None = None,
    ) -> QuorumClosureResult:
        return asyncio.run(
            self.vote_and_maybe_close_async(
                request_id=request_id,
                voter=voter,
                group=group,
                voter_roles=voter_roles,
                approve=approve,
                note=note,
                fencing_token=fencing_token,
                now=now,
            )
        )

    async def vote_and_maybe_close_async(
        self,
        *,
        request_id: str,
        voter: str,
        group: str,
        voter_roles: tuple[str, ...],
        approve: bool,
        note: str,
        fencing_token: int,
        now: int | None = None,
    ) -> QuorumClosureResult:
        current = int(
            now if now is not None
            else time.time()
        )
        request = (
            self.approval_repository.get(
                request_id
            )
        )
        if request is None:
            raise KeyError(
                "Onay talebi bulunamadı"
            )
        if request.requested_by == voter:
            raise ValueError(
                "Talebi oluşturan kullanıcı "
                "oy kullanamaz"
            )
        if group not in voter_roles:
            raise ValueError(
                "Oy grubu kullanıcının "
                "doğrulanmış rolleri arasında değil"
            )

        self.quorum_repository.cast_vote(
            request_id=request_id,
            voter=voter,
            group=group,
            approve=approve,
            note=note,
            now=current,
        )
        decision = (
            self.quorum_repository.decision(
                request_id
            )
        )

        if decision.status != "APPROVED":
            return QuorumClosureResult(
                request_id=request_id,
                claim_id=request.claim_id,
                status=decision.status,
                approvals=decision.approvals,
                rejections=decision.rejections,
                groups=decision.groups,
                closed=False,
                reason=(
                    "Talep reddedildi"
                    if decision.status
                    == "REJECTED"
                    else "Quorum bekleniyor"
                ),
                created_at=current,
            )

        created, execution = (
            self.execution_repository.claim(
                request_id=request_id,
                claim_id=request.claim_id,
                owner=voter,
                now=current,
            )
        )

        if not created:
            if execution.status == "COMPLETED":
                return QuorumClosureResult(
                    request_id=request_id,
                    claim_id=request.claim_id,
                    status=decision.status,
                    approvals=decision.approvals,
                    rejections=decision.rejections,
                    groups=decision.groups,
                    closed=(
                        execution.result_status
                        == "CLOSED"
                    ),
                    reason=(
                        execution.reason
                        or "Kapatma daha önce tamamlandı"
                    ),
                    created_at=current,
                )

            return QuorumClosureResult(
                request_id=request_id,
                claim_id=request.claim_id,
                status="IN_PROGRESS",
                approvals=decision.approvals,
                rejections=decision.rejections,
                groups=decision.groups,
                closed=False,
                reason=(
                    "Kapatma başka worker "
                    "tarafından yürütülüyor"
                ),
                created_at=current,
            )

        guarded = await self.execution_guard.run(
            record=execution,
            operation=lambda: (
                self.closure_service.close(
                    claim_id=request.claim_id,
                    operator=voter,
                    note=note,
                    fencing_token=fencing_token,
                    now=current,
                )
            ),
        )

        if guarded.ownership_lost:
            return QuorumClosureResult(
                request_id=request_id,
                claim_id=request.claim_id,
                status="OWNERSHIP_LOST",
                approvals=decision.approvals,
                rejections=decision.rejections,
                groups=decision.groups,
                closed=False,
                reason=(
                    guarded.error
                    or "Execution ownership kaybedildi"
                ),
                created_at=current,
                ownership_lost=True,
            )

        if guarded.error is not None:
            return QuorumClosureResult(
                request_id=request_id,
                claim_id=request.claim_id,
                status="FAILED",
                approvals=decision.approvals,
                rejections=decision.rejections,
                groups=decision.groups,
                closed=False,
                reason=guarded.error,
                created_at=current,
            )

        closure = guarded.result

        try:
            completed = (
                self.execution_repository.complete(
                    record=execution,
                    result_status=closure.status,
                    reason=closure.reason,
                    now=current,
                )
            )
        except ExecutionOwnershipLost as exc:
            return QuorumClosureResult(
                request_id=request_id,
                claim_id=request.claim_id,
                status="OWNERSHIP_LOST",
                approvals=decision.approvals,
                rejections=decision.rejections,
                groups=decision.groups,
                closed=False,
                reason=str(exc),
                created_at=current,
                ownership_lost=True,
            )

        return QuorumClosureResult(
            request_id=request_id,
            claim_id=request.claim_id,
            status=decision.status,
            approvals=decision.approvals,
            rejections=decision.rejections,
            groups=decision.groups,
            closed=(
                completed.result_status
                == "CLOSED"
            ),
            reason=(
                completed.reason
                or closure.reason
            ),
            created_at=current,
        )
