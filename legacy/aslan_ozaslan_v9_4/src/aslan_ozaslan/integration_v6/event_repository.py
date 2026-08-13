from __future__ import annotations
import json
from pathlib import Path

from .provider_events import ProviderEventRecord

class ProviderEventRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load_all(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def upsert(self, record: ProviderEventRecord) -> bool:
        record.validate()
        data = self._load_all()
        key = f"{record.fixture_id}:{record.provider_event_id}"

        payload = {
            "fixture_id": record.fixture_id,
            "minute": record.minute,
            "team_id": record.team_id,
            "event_type": record.event_type,
            "value": record.value,
            "corrected": record.corrected,
            "cancelled": record.cancelled,
        }

        changed = data.get(key) != payload
        data[key] = payload

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)
        return changed

    def for_fixture(self, fixture_id: str) -> tuple[ProviderEventRecord, ...]:
        data = self._load_all()
        records = []
        for key, item in data.items():
            if item["fixture_id"] != fixture_id:
                continue
            provider_event_id = key.split(":", 1)[1]
            records.append(
                ProviderEventRecord(
                    provider_event_id=provider_event_id,
                    fixture_id=item["fixture_id"],
                    minute=int(item["minute"]),
                    team_id=item["team_id"],
                    event_type=item["event_type"],
                    value=float(item["value"]),
                    corrected=bool(item["corrected"]),
                    cancelled=bool(item["cancelled"]),
                )
            )
        return tuple(
            sorted(records, key=lambda item: (item.minute, item.provider_event_id))
        )
