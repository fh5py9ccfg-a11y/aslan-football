from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ReleaseApproval:
    release_version: str
    approver_id: str
    approved_at: str
    comment: str


class ReleaseApprovalWorkflow:
    def __init__(self, minimum_approvals: int = 2):
        if minimum_approvals <= 0:
            raise ValueError("minimum_approvals pozitif olmalıdır")
        self.minimum_approvals = minimum_approvals
        self._approvals: dict[str, dict[str, ReleaseApproval]] = {}

    def approve(
        self,
        *,
        release_version: str,
        approver_id: str,
        comment: str = "",
    ) -> ReleaseApproval:
        if not release_version.strip() or not approver_id.strip():
            raise ValueError("Release ve approver bilgisi boş olamaz")

        approval = ReleaseApproval(
            release_version=release_version,
            approver_id=approver_id,
            approved_at=datetime.now(timezone.utc).isoformat(),
            comment=comment,
        )
        self._approvals.setdefault(release_version, {})[approver_id] = approval
        return approval

    def is_approved(self, release_version: str) -> bool:
        return (
            len(self._approvals.get(release_version, {}))
            >= self.minimum_approvals
        )

    def approvals(self, release_version: str) -> tuple[ReleaseApproval, ...]:
        return tuple(
            self._approvals.get(release_version, {}).values()
        )
