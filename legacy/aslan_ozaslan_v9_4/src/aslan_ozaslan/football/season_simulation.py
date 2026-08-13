from __future__ import annotations
from dataclasses import dataclass
import random

@dataclass(frozen=True)
class ScheduledFixture:
    home_team_id: str
    away_team_id: str
    home_probability: float
    draw_probability: float
    away_probability: float

@dataclass(frozen=True)
class TeamSeasonProjection:
    team_id: str
    average_points: float
    title_probability: float
    top_four_probability: float
    relegation_probability: float

class MonteCarloSeasonSimulator:
    def simulate(
        self,
        *,
        team_ids: list[str],
        fixtures: list[ScheduledFixture],
        existing_points: dict[str, int] | None = None,
        iterations: int = 1000,
        relegation_places: int = 3,
        seed: int | None = None,
    ) -> tuple[TeamSeasonProjection, ...]:
        if iterations <= 0:
            raise ValueError("iterations pozitif olmalıdır")
        if len(set(team_ids)) != len(team_ids):
            raise ValueError("Takım kimlikleri benzersiz olmalıdır")
        if not team_ids:
            raise ValueError("En az bir takım gereklidir")
        if not 0 <= relegation_places < len(team_ids):
            raise ValueError("Geçersiz relegation_places")

        rng = random.Random(seed)
        points_totals = {team_id: 0 for team_id in team_ids}
        title_counts = {team_id: 0 for team_id in team_ids}
        top_four_counts = {team_id: 0 for team_id in team_ids}
        relegation_counts = {team_id: 0 for team_id in team_ids}
        initial = existing_points or {}

        for fixture in fixtures:
            if fixture.home_team_id not in points_totals or fixture.away_team_id not in points_totals:
                raise ValueError("Fixture içindeki takım bilinmiyor")
            probs = (
                fixture.home_probability,
                fixture.draw_probability,
                fixture.away_probability,
            )
            if any(value < 0 or value > 1 for value in probs):
                raise ValueError("Fixture olasılıkları geçersiz")
            if abs(sum(probs) - 1.0) > 1e-6:
                raise ValueError("Fixture olasılık toplamı 1 olmalıdır")

        for _ in range(iterations):
            points = {team_id: int(initial.get(team_id, 0)) for team_id in team_ids}

            for fixture in fixtures:
                value = rng.random()
                if value < fixture.home_probability:
                    points[fixture.home_team_id] += 3
                elif value < fixture.home_probability + fixture.draw_probability:
                    points[fixture.home_team_id] += 1
                    points[fixture.away_team_id] += 1
                else:
                    points[fixture.away_team_id] += 3

            ranking = sorted(team_ids, key=lambda team_id: (-points[team_id], team_id))
            for team_id in team_ids:
                points_totals[team_id] += points[team_id]

            title_counts[ranking[0]] += 1
            for team_id in ranking[:min(4, len(ranking))]:
                top_four_counts[team_id] += 1
            if relegation_places:
                for team_id in ranking[-relegation_places:]:
                    relegation_counts[team_id] += 1

        projections = [
            TeamSeasonProjection(
                team_id=team_id,
                average_points=points_totals[team_id] / iterations,
                title_probability=title_counts[team_id] / iterations,
                top_four_probability=top_four_counts[team_id] / iterations,
                relegation_probability=relegation_counts[team_id] / iterations,
            )
            for team_id in team_ids
        ]
        return tuple(sorted(projections, key=lambda item: -item.average_points))
