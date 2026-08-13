from __future__ import annotations
from dataclasses import dataclass
from math import sqrt

from .domain import PlayerDNA

@dataclass(frozen=True)
class DNASimilarity:
    player_id: str
    similarity: float

class PlayerDNAAnalyzer:
    def similarity(
        self,
        target: PlayerDNA,
        candidates: list[PlayerDNA],
        *,
        limit: int = 5,
    ) -> tuple[DNASimilarity, ...]:
        target.validate()
        if limit <= 0:
            raise ValueError("limit pozitif olmalıdır")

        target_vector = self._vector(target)
        results = []

        for candidate in candidates:
            candidate.validate()
            if candidate.player_id == target.player_id:
                continue

            candidate_vector = self._vector(candidate)
            distance = sqrt(sum(
                (a - b) ** 2
                for a, b in zip(target_vector, candidate_vector)
            ))
            similarity = 1.0 / (1.0 + distance)
            results.append(
                DNASimilarity(candidate.player_id, similarity)
            )

        return tuple(sorted(
            results,
            key=lambda item: (-item.similarity, item.player_id),
        )[:limit])

    def _vector(self, item: PlayerDNA) -> tuple[float, ...]:
        return (
            item.passing,
            item.progression,
            item.dribbling,
            item.pressing,
            item.defending,
            item.aerial,
            item.finishing,
            item.creativity,
            item.athleticism,
            item.consistency,
        )
