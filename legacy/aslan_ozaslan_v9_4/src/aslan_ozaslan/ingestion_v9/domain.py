from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class IngestionRecord:
    provider: str
    payload_type: str
    external_id: str
    payload_hash: str
    status: str
    attempt_count: int
    last_error: str | None = None

@dataclass(frozen=True)
class IngestionItemResult:
    payload_type: str
    external_id: str | None
    accepted: bool
    duplicate: bool
    archived: bool
    projected: bool
    quarantined: bool
    reason: str

@dataclass(frozen=True)
class BatchIngestionReport:
    total: int
    accepted: int
    duplicates: int
    quarantined: int
    failed: int
    results: tuple[IngestionItemResult, ...]
