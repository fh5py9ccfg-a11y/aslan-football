import pytest

from apps.api.app.mvp_workspace import (
    MVPValidationError,
    MVPWorkspaceService,
    RedisMVPRepository,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


def test_short_tactical_plan_is_rejected():
    service = MVPWorkspaceService(
        repository=RedisMVPRepository(
            Redis(),
            prefix="mvp",
        )
    )
    service.create_club(
        club_id="c1",
        name="Club",
        country="TR",
        now=100,
    )
    service.create_match(
        match_id="m1",
        club_id="c1",
        opponent="Opponent",
        competition="League",
        kickoff_at=300,
        venue="HOME",
        now=101,
    )
    service.save_opponent_profile(
        opponent_id="o1",
        club_id="c1",
        name="Opponent",
        formation="4-4-2",
        strengths=(),
        weaknesses=(),
        key_players=(),
        notes="",
        now=102,
    )

    with pytest.raises(MVPValidationError):
        service.create_match_preparation(
            preparation_id="prep1",
            match_id="m1",
            club_id="c1",
            opponent_id="o1",
            tactical_plan="x",
            pressing_plan="",
            set_piece_plan="",
            objectives=(),
            now=103,
        )
