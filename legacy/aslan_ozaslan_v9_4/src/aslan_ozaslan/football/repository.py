from __future__ import annotations
from .domain import League, Team, MatchResult

class FootballRepository:
    def __init__(self):
        self._leagues = {}
        self._teams = {}
        self._matches = {}

    def add_league(self, league: League) -> None:
        if not league.league_id.strip():
            raise ValueError("league_id boş olamaz")
        self._leagues[league.league_id] = league

    def add_team(self, team: Team) -> None:
        if team.league_id not in self._leagues:
            raise ValueError("Takım bilinmeyen lige bağlanamaz")
        self._teams[team.team_id] = team

    def add_match(self, match: MatchResult) -> None:
        match.validate()
        if match.league_id not in self._leagues:
            raise ValueError("Maç bilinmeyen lige bağlanamaz")
        if match.home_team_id not in self._teams or match.away_team_id not in self._teams:
            raise ValueError("Maçtaki takımlar bulunmalıdır")
        self._matches[match.match_id] = match

    def matches_for_team(self, team_id: str, limit: int | None = None):
        items = [m for m in self._matches.values()
                 if team_id in (m.home_team_id, m.away_team_id)]
        items.sort(key=lambda m: m.played_at, reverse=True)
        return items if limit is None else items[:limit]

    def matches_for_league(self, league_id: str):
        return sorted(
            [m for m in self._matches.values() if m.league_id == league_id],
            key=lambda m: m.played_at,
        )
