from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class NormalizedLiveFixture:
    provider_fixture_id: str
    state: str | None
    minute: int | None
    home_team_id: str | None
    away_team_id: str | None
    home_score: int | None
    away_score: int | None
    raw: dict

class SportmonksNormalizer:
    def normalize_live_fixture(self, item: dict) -> NormalizedLiveFixture:
        participants = item.get("participants") or []
        home = next(
            (p for p in participants if (p.get("meta") or {}).get("location") == "home"),
            None,
        )
        away = next(
            (p for p in participants if (p.get("meta") or {}).get("location") == "away"),
            None,
        )

        scores = item.get("scores") or []
        current = [
            score for score in scores
            if (score.get("description") or "").upper() in {
                "CURRENT", "2ND_HALF", "1ST_HALF"
            }
        ]

        home_score = away_score = None
        for score in current:
            participant = score.get("participant")
            goals = (score.get("score") or {}).get("goals")
            if participant == "home":
                home_score = goals
            elif participant == "away":
                away_score = goals

        state = item.get("state")
        if isinstance(state, dict):
            state = state.get("short_name") or state.get("name")

        minute = item.get("minutes")
        if minute is None:
            minute = item.get("minute")

        return NormalizedLiveFixture(
            provider_fixture_id=str(item.get("id")),
            state=state,
            minute=int(minute) if minute is not None else None,
            home_team_id=str(home.get("id")) if home else None,
            away_team_id=str(away.get("id")) if away else None,
            home_score=int(home_score) if home_score is not None else None,
            away_score=int(away_score) if away_score is not None else None,
            raw=dict(item),
        )
