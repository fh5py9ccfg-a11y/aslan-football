from dataclasses import dataclass
import time

@dataclass(frozen=True)
class QuarantineRetryResult:
    claim_id: str
    index_key: str
    phase: str
    status: str
    removed: int
    repaired: int
    error: str | None
    completed_at: int

class QuarantineRetryService:
    def __init__(self, *, diagnostic_service, maintainer_factory):
        self.diagnostic_service = diagnostic_service
        self.maintainer_factory = maintainer_factory

    def retry(self, *, claim_id, now=None):
        current = int(now if now is not None else time.time())
        diagnostic = self.diagnostic_service.inspect(
            claim_id,
            now=current,
        )
        if diagnostic.error:
            return QuarantineRetryResult(
                claim_id=claim_id,
                index_key=diagnostic.index_key,
                phase=diagnostic.phase,
                status="FAILED",
                removed=0,
                repaired=0,
                error=diagnostic.error,
                completed_at=current,
            )
        try:
            removed, repaired = self.maintainer_factory()._clean_index(
                diagnostic.index_key
            )
            return QuarantineRetryResult(
                claim_id=claim_id,
                index_key=diagnostic.index_key,
                phase=diagnostic.phase,
                status="SUCCEEDED",
                removed=removed,
                repaired=repaired,
                error=None,
                completed_at=current,
            )
        except Exception as exc:
            return QuarantineRetryResult(
                claim_id=claim_id,
                index_key=diagnostic.index_key,
                phase=diagnostic.phase,
                status="FAILED",
                removed=0,
                repaired=0,
                error=str(exc),
                completed_at=current,
            )
