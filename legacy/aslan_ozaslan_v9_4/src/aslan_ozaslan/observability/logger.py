from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

class JsonEventLogger:
    REDACT_KEYS = {"password", "password_hash", "token", "session_token", "api_key", "secret"}

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event_type: str, payload: dict[str, Any]) -> None:
        safe_payload = {
            key: ("[REDACTED]" if key.lower() in self.REDACT_KEYS else value)
            for key, value in payload.items()
        }
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": safe_payload,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
