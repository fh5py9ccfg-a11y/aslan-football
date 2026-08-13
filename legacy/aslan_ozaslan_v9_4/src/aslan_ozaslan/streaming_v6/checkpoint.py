from __future__ import annotations
import json
from pathlib import Path

from .domain import StreamCheckpoint

class JsonCheckpointRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self, stream_id: str) -> StreamCheckpoint:
        if not self.path.exists():
            return StreamCheckpoint(stream_id, -1, 0, 0)

        data = json.loads(self.path.read_text(encoding="utf-8"))
        item = data.get(stream_id)
        if item is None:
            return StreamCheckpoint(stream_id, -1, 0, 0)

        return StreamCheckpoint(
            stream_id=stream_id,
            last_sequence=int(item["last_sequence"]),
            processed_events=int(item["processed_events"]),
            corrected_events=int(item["corrected_events"]),
        )

    def save(self, checkpoint: StreamCheckpoint) -> None:
        data = {}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))

        data[checkpoint.stream_id] = {
            "last_sequence": checkpoint.last_sequence,
            "processed_events": checkpoint.processed_events,
            "corrected_events": checkpoint.corrected_events,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)
