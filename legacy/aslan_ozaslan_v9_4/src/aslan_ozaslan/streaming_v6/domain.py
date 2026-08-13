from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class StreamEnvelope:
    stream_id: str
    sequence: int
    event_id: str
    payload_type: str
    payload: dict
    occurred_at: float

    def validate(self) -> None:
        if not self.stream_id.strip() or not self.event_id.strip():
            raise ValueError("stream_id ve event_id boş olamaz")
        if self.sequence < 0:
            raise ValueError("sequence negatif olamaz")
        if self.occurred_at < 0:
            raise ValueError("occurred_at negatif olamaz")
        if self.payload_type not in {"EVENT", "CORRECTION", "HEARTBEAT"}:
            raise ValueError("Desteklenmeyen payload_type")

@dataclass(frozen=True)
class StreamCheckpoint:
    stream_id: str
    last_sequence: int
    processed_events: int
    corrected_events: int
