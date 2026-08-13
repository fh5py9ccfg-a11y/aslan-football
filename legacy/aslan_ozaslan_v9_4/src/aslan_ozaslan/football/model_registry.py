from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class FootballModelVersion:
    model_name: str
    version: str
    league_id: str
    trained_at: str
    brier_score: float
    log_loss: float
    active: bool

class FootballModelRegistry:
    def __init__(self):
        self._versions: dict[tuple[str, str, str], FootballModelVersion] = {}

    def register(
        self,
        *,
        model_name: str,
        version: str,
        league_id: str,
        brier_score: float,
        log_loss: float,
    ) -> FootballModelVersion:
        if not all(value.strip() for value in (model_name, version, league_id)):
            raise ValueError("Model kimlik alanları boş olamaz")
        if brier_score < 0 or log_loss < 0:
            raise ValueError("Model metrikleri negatif olamaz")

        record = FootballModelVersion(
            model_name=model_name,
            version=version,
            league_id=league_id,
            trained_at=datetime.now(timezone.utc).isoformat(),
            brier_score=brier_score,
            log_loss=log_loss,
            active=False,
        )
        self._versions[(model_name, version, league_id)] = record
        return record

    def activate(self, model_name: str, version: str, league_id: str) -> FootballModelVersion:
        key = (model_name, version, league_id)
        if key not in self._versions:
            raise KeyError("Model sürümü bulunamadı")

        for current_key, current in list(self._versions.items()):
            if current.model_name == model_name and current.league_id == league_id:
                self._versions[current_key] = FootballModelVersion(
                    current.model_name,
                    current.version,
                    current.league_id,
                    current.trained_at,
                    current.brier_score,
                    current.log_loss,
                    current_key == key,
                )
        return self._versions[key]

    def active(self, model_name: str, league_id: str) -> FootballModelVersion | None:
        for item in self._versions.values():
            if item.model_name == model_name and item.league_id == league_id and item.active:
                return item
        return None
