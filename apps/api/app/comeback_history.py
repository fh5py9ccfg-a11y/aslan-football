from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Iterable, Mapping

from sqlalchemy import select

from .db import SessionLocal
from .models import FixtureModel, MatchEventModel


FINISHED_STATUSES = {
    "finished",
    "ft",
    "after extra time",
    "after penalties",
    "aet",
    "pen",
}


@dataclass(frozen=True)
class TeamComebackProfile:
    team: str
    matches: int
    halftime_behind: int
    halftime_behind_wins: int
    halftime_ahead: int
    halftime_ahead_losses: int
    goals_scored: int
    second_half_goals_scored: int
    home_2_1_matches: int
    away_1_2_matches: int

    @property
    def comeback_rate_when_behind(self) -> float:
        return self.halftime_behind_wins / self.halftime_behind if self.halftime_behind else 0.0

    @property
    def loss_rate_when_ahead(self) -> float:
        return self.halftime_ahead_losses / self.halftime_ahead if self.halftime_ahead else 0.0

    @property
    def second_half_goal_share(self) -> float:
        return self.second_half_goals_scored / self.goals_scored if self.goals_scored else 0.5

    @property
    def home_2_1_rate(self) -> float:
        return self.home_2_1_matches / self.matches if self.matches else 0.0

    @property
    def away_1_2_rate(self) -> float:
        return self.away_1_2_matches / self.matches if self.matches else 0.0

    def as_dict(self) -> dict:
        value = asdict(self)
        value.update(
            comeback_rate_when_behind=round(self.comeback_rate_when_behind, 4),
            loss_rate_when_ahead=round(self.loss_rate_when_ahead, 4),
            second_half_goal_share=round(self.second_half_goal_share, 4),
            home_2_1_rate=round(self.home_2_1_rate, 4),
            away_1_2_rate=round(self.away_1_2_rate, 4),
        )
        return value


def _norm_team(value: object) -> str:
    return str(value or "").strip()


def _result(home: int, away: int) -> str:
    if home > away:
        return "HOME"
    if away > home:
        return "AWAY"
    return "DRAW"


def build_team_comeback_profiles(
    teams: Iterable[str],
    *,
    lookback_days: int = 730,
    minimum_kickoff: datetime | None = None,
) -> dict[str, TeamComebackProfile]:
    wanted = {_norm_team(team) for team in teams if _norm_team(team)}
    if not wanted:
        return {}

    now = datetime.now(timezone.utc)
    cutoff = minimum_kickoff or (now - timedelta(days=max(30, int(lookback_days))))

    with SessionLocal() as session:
        fixtures = session.execute(
            select(FixtureModel).where(
                FixtureModel.kickoff_at >= cutoff,
                FixtureModel.kickoff_at < now,
            )
        ).scalars().all()

        fixtures = [
            item
            for item in fixtures
            if (
                _norm_team(item.home_team) in wanted
                or _norm_team(item.away_team) in wanted
            )
            and str(item.status or "").strip().lower() in FINISHED_STATUSES
        ]
        fixture_ids = [item.fixture_id for item in fixtures]
        if not fixture_ids:
            return {}

        events = session.execute(
            select(MatchEventModel).where(
                MatchEventModel.fixture_id.in_(fixture_ids),
                MatchEventModel.event_type == "GOAL",
            )
        ).scalars().all()

    goals_by_fixture: dict[str, list[MatchEventModel]] = defaultdict(list)
    for event in events:
        goals_by_fixture[event.fixture_id].append(event)

    counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for fixture in fixtures:
        home = _norm_team(fixture.home_team)
        away = _norm_team(fixture.away_team)
        home_ht = away_ht = home_ft = away_ft = 0
        home_second = away_second = 0

        for event in goals_by_fixture.get(fixture.fixture_id, ()):
            side = str(event.team or "").upper()
            if side not in {"HOME", "AWAY"}:
                continue
            minute = int(event.minute or 0)
            if side == "HOME":
                home_ft += 1
                if minute <= 45:
                    home_ht += 1
                else:
                    home_second += 1
            else:
                away_ft += 1
                if minute <= 45:
                    away_ht += 1
                else:
                    away_second += 1

        ht_result = _result(home_ht, away_ht)
        ft_result = _result(home_ft, away_ft)

        for team, side in ((home, "HOME"), (away, "AWAY")):
            if team not in wanted:
                continue
            c = counters[team]
            c["matches"] += 1
            if side == "HOME":
                c["goals_scored"] += home_ft
                c["second_half_goals_scored"] += home_second
                if ht_result == "AWAY":
                    c["halftime_behind"] += 1
                    if ft_result == "HOME":
                        c["halftime_behind_wins"] += 1
                        c["home_2_1_matches"] += 1
                if ht_result == "HOME":
                    c["halftime_ahead"] += 1
                    if ft_result == "AWAY":
                        c["halftime_ahead_losses"] += 1
            else:
                c["goals_scored"] += away_ft
                c["second_half_goals_scored"] += away_second
                if ht_result == "HOME":
                    c["halftime_behind"] += 1
                    if ft_result == "AWAY":
                        c["halftime_behind_wins"] += 1
                        c["away_1_2_matches"] += 1
                if ht_result == "AWAY":
                    c["halftime_ahead"] += 1
                    if ft_result == "HOME":
                        c["halftime_ahead_losses"] += 1

    result: dict[str, TeamComebackProfile] = {}
    for team, c in counters.items():
        result[team] = TeamComebackProfile(
            team=team,
            matches=c["matches"],
            halftime_behind=c["halftime_behind"],
            halftime_behind_wins=c["halftime_behind_wins"],
            halftime_ahead=c["halftime_ahead"],
            halftime_ahead_losses=c["halftime_ahead_losses"],
            goals_scored=c["goals_scored"],
            second_half_goals_scored=c["second_half_goals_scored"],
            home_2_1_matches=c["home_2_1_matches"],
            away_1_2_matches=c["away_1_2_matches"],
        )
    return result


def enrich_fixtures_with_history(
    fixtures: list[dict],
    *,
    lookback_days: int = 730,
) -> list[dict]:
    teams = {
        _norm_team(value)
        for fixture in fixtures
        for value in (fixture.get("home_team"), fixture.get("away_team"))
        if _norm_team(value)
    }
    profiles = build_team_comeback_profiles(teams, lookback_days=lookback_days)

    enriched: list[dict] = []
    for fixture in fixtures:
        item = dict(fixture)
        inputs = dict(item.get("comeback_inputs") or {})
        home = profiles.get(_norm_team(item.get("home_team")))
        away = profiles.get(_norm_team(item.get("away_team")))

        if home is not None:
            inputs.setdefault("home_comeback_rate_when_behind", home.comeback_rate_when_behind)
            inputs.setdefault("home_loss_rate_when_ahead", home.loss_rate_when_ahead)
            inputs.setdefault("home_second_half_goal_share", home.second_half_goal_share)
            inputs.setdefault("historical_2_1_rate", home.home_2_1_rate)
            item["home_history_profile"] = home.as_dict()
        if away is not None:
            inputs.setdefault("away_comeback_rate_when_behind", away.comeback_rate_when_behind)
            inputs.setdefault("away_loss_rate_when_ahead", away.loss_rate_when_ahead)
            inputs.setdefault("away_second_half_goal_share", away.second_half_goal_share)
            inputs.setdefault("historical_1_2_rate", away.away_1_2_rate)
            item["away_history_profile"] = away.as_dict()

        item["comeback_inputs"] = inputs
        item["history_ready"] = bool(home and away)
        enriched.append(item)

    return enriched
