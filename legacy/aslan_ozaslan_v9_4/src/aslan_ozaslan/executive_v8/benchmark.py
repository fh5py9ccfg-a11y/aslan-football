from __future__ import annotations
from dataclasses import dataclass

from .domain import ClubExecutiveSnapshot

@dataclass(frozen=True)
class ClubBenchmark:
    club_id: str
    composite_score: float
    sporting_rank: int
    financial_rank: int
    overall_rank: int

class MultiClubBenchmarkEngine:
    def compare(
        self,
        snapshots: list[ClubExecutiveSnapshot],
    ) -> tuple[ClubBenchmark, ...]:
        if not snapshots:
            raise ValueError("Karşılaştırma için kulüp gerekir")
        for item in snapshots:
            item.validate()

        sporting_order = sorted(
            snapshots,
            key=lambda item: (-item.sporting_score, item.club_id),
        )
        financial_order = sorted(
            snapshots,
            key=lambda item: (-item.financial_score, item.club_id),
        )

        sporting_rank = {
            item.club_id: index + 1
            for index, item in enumerate(sporting_order)
        }
        financial_rank = {
            item.club_id: index + 1
            for index, item in enumerate(financial_order)
        }

        composite = []
        for item in snapshots:
            score = (
                item.sporting_score * 0.28
                + item.financial_score * 0.20
                + item.squad_score * 0.18
                + item.academy_score * 0.12
                + item.transfer_score * 0.12
                + (1.0 - item.risk_score) * 0.10
            )
            composite.append((item, score))

        overall_order = sorted(
            composite,
            key=lambda pair: (-pair[1], pair[0].club_id),
        )
        overall_rank = {
            item.club_id: index + 1
            for index, (item, _) in enumerate(overall_order)
        }

        return tuple(
            ClubBenchmark(
                club_id=item.club_id,
                composite_score=score,
                sporting_rank=sporting_rank[item.club_id],
                financial_rank=financial_rank[item.club_id],
                overall_rank=overall_rank[item.club_id],
            )
            for item, score in overall_order
        )
