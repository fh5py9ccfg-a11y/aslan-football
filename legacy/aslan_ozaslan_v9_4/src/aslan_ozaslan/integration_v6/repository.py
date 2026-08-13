from __future__ import annotations
import json
from pathlib import Path

from .domain import ProviderFixtureSnapshot

class FixtureSnapshotRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self, fixture_id: str) -> ProviderFixtureSnapshot | None:
        if not self.path.exists():
            return None

        data = json.loads(self.path.read_text(encoding="utf-8"))
        item = data.get(fixture_id)
        if item is None:
            return None

        return ProviderFixtureSnapshot(
            fixture_id=fixture_id,
            minute=int(item["minute"]),
            home_team_id=str(item["home_team_id"]),
            away_team_id=str(item["away_team_id"]),
            home_score=int(item["home_score"]),
            away_score=int(item["away_score"]),
            state=str(item["state"]),
            updated_at=str(item["updated_at"]),
        )

    def save(self, snapshot: ProviderFixtureSnapshot) -> None:
        data = {}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))

        data[snapshot.fixture_id] = {
            "minute": snapshot.minute,
            "home_team_id": snapshot.home_team_id,
            "away_team_id": snapshot.away_team_id,
            "home_score": snapshot.home_score,
            "away_score": snapshot.away_score,
            "state": snapshot.state,
            "updated_at": snapshot.updated_at,
        }

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)
