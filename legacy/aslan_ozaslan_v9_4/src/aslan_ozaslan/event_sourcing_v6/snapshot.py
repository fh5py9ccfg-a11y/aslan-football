import json
from pathlib import Path
from .domain import AggregateSnapshot, MatchAggregateState

class JsonSnapshotRepository:
    def __init__(self, path):
        self.path = Path(path)

    def save(self, snapshot):
        data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        s = snapshot.state
        data[snapshot.fixture_id] = {
            "last_sequence": snapshot.last_sequence,
            "state": s.__dict__,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def load(self, fixture_id):
        if not self.path.exists():
            return None
        item = json.loads(self.path.read_text(encoding="utf-8")).get(fixture_id)
        if item is None:
            return None
        state = MatchAggregateState(**item["state"])
        return AggregateSnapshot(fixture_id, int(item["last_sequence"]), state)
