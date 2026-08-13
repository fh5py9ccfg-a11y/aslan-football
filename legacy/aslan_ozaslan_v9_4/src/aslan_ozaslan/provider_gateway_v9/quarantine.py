from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

class PayloadQuarantineRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def add(
        self,
        *,
        payload_type: str,
        payload: dict,
        errors: tuple[str, ...],
        warnings: tuple[str, ...] = (),
    ) -> None:
        data = []
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))

        data.append({
            "payload_type": payload_type,
            "payload": payload,
            "errors": list(errors),
            "warnings": list(warnings),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def list_all(self) -> tuple[dict, ...]:
        if not self.path.exists():
            return ()
        return tuple(json.loads(self.path.read_text(encoding="utf-8")))
