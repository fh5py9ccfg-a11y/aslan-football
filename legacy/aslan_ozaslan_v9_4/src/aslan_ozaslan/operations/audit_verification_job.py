from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditVerificationResult:
    valid: bool
    checked_repository: str
    message: str


class AuditVerificationJob:
    def __init__(self, repository, repository_name: str = "audit"):
        self.repository = repository
        self.repository_name = repository_name

    def run(self) -> AuditVerificationResult:
        valid = bool(self.repository.verify_chain())
        return AuditVerificationResult(
            valid=valid,
            checked_repository=self.repository_name,
            message=(
                "Audit zinciri doğrulandı"
                if valid
                else "Audit zinciri bütünlük kontrolünden geçemedi"
            ),
        )
