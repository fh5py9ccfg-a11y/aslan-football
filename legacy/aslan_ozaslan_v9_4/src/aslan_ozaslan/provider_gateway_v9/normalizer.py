from __future__ import annotations

from .domain import (
    NormalizedFixturePayload,
    NormalizedPlayerPayload,
    NormalizedProviderEvent,
)

class SportmonksPayloadNormalizer:
    EVENT_TYPE_MAP = {
        "goal": "GOAL",
        "yellowcard": "YELLOW_CARD",
        "redcard": "RED_CARD",
        "substitution": "SUBSTITUTION",
        "var": "VAR",
        "penalty": "PENALTY",
        "missed_penalty": "MISSED_PENALTY",
    }

    def fixture(self, payload: dict) -> NormalizedFixturePayload:
        participants = payload.get("participants") or []
        home = next(
            (
                item for item in participants
                if str(item.get("meta", {}).get("location", "")).lower() == "home"
            ),
            None,
        )
        away = next(
            (
                item for item in participants
                if str(item.get("meta", {}).get("location", "")).lower() == "away"
            ),
            None,
        )

        if home is None or away is None:
            if len(participants) >= 2:
                home, away = participants[0], participants[1]
            else:
                raise ValueError("Fixture katılımcıları normalize edilemedi")

        scores = payload.get("scores") or []
        home_score = self._score_for(scores, home.get("id"))
        away_score = self._score_for(scores, away.get("id"))
        state = payload.get("state") or {}

        return NormalizedFixturePayload(
            fixture_id=str(payload["id"]),
            league_id=(
                str(payload["league_id"])
                if payload.get("league_id") is not None
                else None
            ),
            season_id=(
                str(payload["season_id"])
                if payload.get("season_id") is not None
                else None
            ),
            home_team_id=str(home["id"]),
            away_team_id=str(away["id"]),
            state=str(
                state.get("developer_name")
                or state.get("name")
                or payload.get("state_id")
                or "UNKNOWN"
            ),
            minute=(
                int(state["minute"])
                if state.get("minute") is not None
                else None
            ),
            home_score=home_score,
            away_score=away_score,
            starting_at=payload.get("starting_at"),
            raw=dict(payload),
        )

    def player(self, payload: dict) -> NormalizedPlayerPayload:
        return NormalizedPlayerPayload(
            player_id=str(payload["id"]),
            name=str(
                payload.get("display_name")
                or payload.get("name")
            ),
            team_id=(
                str(payload["team_id"])
                if payload.get("team_id") is not None
                else None
            ),
            position_id=(
                str(payload["position_id"])
                if payload.get("position_id") is not None
                else None
            ),
            nationality_id=(
                str(payload["nationality_id"])
                if payload.get("nationality_id") is not None
                else None
            ),
            date_of_birth=payload.get("date_of_birth"),
            raw=dict(payload),
        )

    def event(self, payload: dict) -> NormalizedProviderEvent:
        raw_type = str(
            payload.get("type", {}).get("developer_name")
            or payload.get("type_name")
            or payload.get("type")
            or ""
        ).lower()
        mapped = self.EVENT_TYPE_MAP.get(raw_type, "UNKNOWN")

        return NormalizedProviderEvent(
            event_id=str(payload["id"]),
            fixture_id=str(payload["fixture_id"]),
            team_id=(
                str(payload["participant_id"])
                if payload.get("participant_id") is not None
                else None
            ),
            player_id=(
                str(payload["player_id"])
                if payload.get("player_id") is not None
                else None
            ),
            event_type=mapped,
            minute=int(payload["minute"]),
            extra_minute=(
                int(payload["extra_minute"])
                if payload.get("extra_minute") is not None
                else None
            ),
            cancelled=bool(
                payload.get("cancelled")
                or payload.get("is_cancelled")
                or False
            ),
            raw=dict(payload),
        )

    def _score_for(self, scores: list[dict], participant_id) -> int | None:
        latest = None
        for item in scores:
            if item.get("participant_id") != participant_id:
                continue
            goals = (item.get("score") or {}).get("goals")
            if goals is not None:
                latest = int(goals)
        return latest
