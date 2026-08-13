from __future__ import annotations
import json
from pathlib import Path

class JsonCheckpointRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self, key: str) -> dict | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return data.get(key)

    def save(self, key: str, value: dict) -> None:
        data = {}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
        data[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)
