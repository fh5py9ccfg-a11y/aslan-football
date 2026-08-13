from __future__ import annotations
import json
from pathlib import Path

class IngestionCheckpointRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(
        self,
        *,
        stream_name: str,
        cursor: str,
        processed_count: int,
    ) -> None:
        data = {}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))

        data[stream_name] = {
            "cursor": cursor,
            "processed_count": processed_count,
        }

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def load(self, stream_name: str) -> dict | None:
        if not self.path.exists():
            return None
        return json.loads(
            self.path.read_text(encoding="utf-8")
        ).get(stream_name)
