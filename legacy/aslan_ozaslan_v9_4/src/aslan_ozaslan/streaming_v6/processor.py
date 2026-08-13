from __future__ import annotations
from dataclasses import dataclass

from .domain import StreamEnvelope, StreamCheckpoint
from .checkpoint import JsonCheckpointRepository
from .event_ledger import EventLedger
from .order_buffer import OrderedEventBuffer

@dataclass(frozen=True)
class StreamProcessResult:
    accepted: bool
    applied_sequences: tuple[int, ...]
    checkpoint: StreamCheckpoint
    pending_count: int

class ResilientStreamProcessor:
    def __init__(
        self,
        *,
        stream_id: str,
        checkpoint_repository: JsonCheckpointRepository,
        ledger: EventLedger | None = None,
    ):
        self.stream_id = stream_id
        self.checkpoints = checkpoint_repository
        self.ledger = ledger or EventLedger()
        checkpoint = self.checkpoints.load(stream_id)
        self.checkpoint = checkpoint
        self.buffer = OrderedEventBuffer(checkpoint.last_sequence + 1)

    def process(self, envelope: StreamEnvelope) -> StreamProcessResult:
        envelope.validate()
        if envelope.stream_id != self.stream_id:
            raise ValueError("Envelope farklı bir stream'e ait")

        ready = self.buffer.push(envelope)
        if not ready:
            return StreamProcessResult(
                accepted=envelope.sequence > self.checkpoint.last_sequence,
                applied_sequences=(),
                checkpoint=self.checkpoint,
                pending_count=self.buffer.pending_count(),
            )

        processed = self.checkpoint.processed_events
        corrected = self.checkpoint.corrected_events
        last_sequence = self.checkpoint.last_sequence
        applied = []

        for item in ready:
            if item.payload_type == "EVENT":
                self.ledger.apply_event(item.event_id, item.payload)
                processed += 1
            elif item.payload_type == "CORRECTION":
                target_id = str(item.payload["target_event_id"])
                corrected_payload = dict(item.payload.get("replacement", {}))
                active = bool(item.payload.get("active", True))
                self.ledger.apply_correction(
                    target_id,
                    corrected_payload,
                    active=active,
                )
                corrected += 1
            elif item.payload_type == "HEARTBEAT":
                pass

            last_sequence = item.sequence
            applied.append(item.sequence)

        self.checkpoint = StreamCheckpoint(
            stream_id=self.stream_id,
            last_sequence=last_sequence,
            processed_events=processed,
            corrected_events=corrected,
        )
        self.checkpoints.save(self.checkpoint)

        return StreamProcessResult(
            accepted=True,
            applied_sequences=tuple(applied),
            checkpoint=self.checkpoint,
            pending_count=self.buffer.pending_count(),
        )
