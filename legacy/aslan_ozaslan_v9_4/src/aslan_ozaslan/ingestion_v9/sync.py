from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SyncPageResult:
    page: int
    processed: int
    accepted: int
    quarantined: int
    next_cursor: str | None

class ProviderPagedSyncService:
    def __init__(
        self,
        *,
        orchestrator,
        checkpoint_repository,
    ):
        self.orchestrator = orchestrator
        self.checkpoints = checkpoint_repository

    def sync_pages(
        self,
        *,
        stream_name: str,
        payload_type: str,
        pages: list[list[dict]],
    ) -> tuple[SyncPageResult, ...]:
        reports = []
        processed_total = 0

        for index, payloads in enumerate(pages, start=1):
            batch = self.orchestrator.ingest_batch(
                payload_type=payload_type,
                payloads=payloads,
            )
            processed_total += batch.total
            next_cursor = (
                str(index + 1)
                if index < len(pages)
                else None
            )
            self.checkpoints.save(
                stream_name=stream_name,
                cursor=next_cursor or "END",
                processed_count=processed_total,
            )
            reports.append(
                SyncPageResult(
                    page=index,
                    processed=batch.total,
                    accepted=batch.accepted,
                    quarantined=batch.quarantined,
                    next_cursor=next_cursor,
                )
            )

        return tuple(reports)
