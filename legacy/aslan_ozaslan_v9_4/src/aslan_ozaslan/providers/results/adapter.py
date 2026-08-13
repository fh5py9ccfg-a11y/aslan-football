from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aslan_ozaslan.results import StoredMatchResult


@dataclass(frozen=True)
class ExternalResult:
    external_fixture_id: str
    home_goals: int
    away_goals: int
    status: str


class ResultProviderAdapter(Protocol):
    name: str

    def completed_results(self) -> list[ExternalResult]:
        ...


class ResultSyncService:
    def __init__(self, adapter: ResultProviderAdapter, identity_map: dict[str, str], repository):
        self.adapter = adapter
        self.identity_map = dict(identity_map)
        self.repository = repository

    def sync(self) -> int:
        saved = 0
        for result in self.adapter.completed_results():
            if result.status != "FINISHED":
                continue
            fixture_id = self.identity_map.get(result.external_fixture_id)
            if fixture_id is None:
                continue
            self.repository.upsert_result(
                StoredMatchResult(
                    fixture_id=fixture_id,
                    home_goals=result.home_goals,
                    away_goals=result.away_goals,
                    source=self.adapter.name,
                )
            )
            saved += 1
        return saved
