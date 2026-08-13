from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

class ProviderRawArchive:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(
        self,
        *,
        provider: str,
        payload_type: str,
        external_id: str,
        payload_hash: str,
        payload: dict,
    ) -> bool:
        entries = []
        if self.path.exists():
            entries = json.loads(self.path.read_text(encoding="utf-8"))

        key = (
            provider,
            payload_type,
            external_id,
            payload_hash,
        )
        for item in entries:
            existing = (
                item["provider"],
                item["payload_type"],
                item["external_id"],
                item["payload_hash"],
            )
            if existing == key:
                return False

        entries.append({
            "provider": provider,
            "payload_type": payload_type,
            "external_id": external_id,
            "payload_hash": payload_hash,
            "payload": payload,
            "archived_at": datetime.now(timezone.utc).isoformat(),
        })

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)
        return True

    def count(self) -> int:
        if not self.path.exists():
            return 0
        return len(json.loads(self.path.read_text(encoding="utf-8")))
