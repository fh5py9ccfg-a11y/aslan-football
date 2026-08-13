from __future__ import annotations

from .domain import StreamEnvelope

class OrderedEventBuffer:
    def __init__(self, expected_sequence: int = 0):
        self.expected_sequence = expected_sequence
        self._pending: dict[int, StreamEnvelope] = {}

    def push(self, envelope: StreamEnvelope) -> tuple[StreamEnvelope, ...]:
        envelope.validate()
        if envelope.sequence < self.expected_sequence:
            return ()
        self._pending.setdefault(envelope.sequence, envelope)

        ready = []
        while self.expected_sequence in self._pending:
            ready.append(self._pending.pop(self.expected_sequence))
            self.expected_sequence += 1
        return tuple(ready)

    def pending_count(self) -> int:
        return len(self._pending)
