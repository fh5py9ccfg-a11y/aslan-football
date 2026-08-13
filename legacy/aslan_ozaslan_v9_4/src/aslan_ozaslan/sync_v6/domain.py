from dataclasses import dataclass
@dataclass(frozen=True)
class SyncCursor:
    provider:str; resource:str; page:int; updated_since:str|None; completed:bool
@dataclass(frozen=True)
class SyncMetrics:
    requests:int; successes:int; failures:int; fixtures_seen:int; fixtures_updated:int; fixtures_skipped:int; average_latency_ms:float
@dataclass(frozen=True)
class SyncRunReport:
    cursor:SyncCursor; metrics:SyncMetrics; integrity_errors:tuple[str,...]; completed:bool
