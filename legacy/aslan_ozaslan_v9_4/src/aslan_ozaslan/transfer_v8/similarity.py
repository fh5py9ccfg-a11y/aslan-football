from __future__ import annotations
from dataclasses import dataclass
from math import sqrt

@dataclass(frozen=True)
class PlayerVector:
    player_id: str
    features: tuple[float, ...]

@dataclass(frozen=True)
class SimilarPlayer:
    player_id: str
    similarity: float

class SimilarPlayerFinder:
    def find(
        self,
        target: PlayerVector,
        candidates: list[PlayerVector],
        *,
        limit: int = 5,
    ) -> tuple[SimilarPlayer, ...]:
        if limit <= 0:
            raise ValueError("limit pozitif olmalıdır")
        if not target.features:
            raise ValueError("Target features boş olamaz")

        results = []
        for candidate in candidates:
            if candidate.player_id == target.player_id:
                continue
            if len(candidate.features) != len(target.features):
                raise ValueError("Feature boyutları eşit olmalıdır")

            distance = sqrt(sum(
                (a - b) ** 2
                for a, b in zip(target.features, candidate.features)
            ))
            similarity = 1.0 / (1.0 + distance)
            results.append(
                SimilarPlayer(candidate.player_id, similarity)
            )

        return tuple(
            sorted(
                results,
                key=lambda item: (-item.similarity, item.player_id),
            )[:limit]
        )
