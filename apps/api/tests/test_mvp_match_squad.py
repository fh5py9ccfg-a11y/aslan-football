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


def build():
    return MVPWorkspaceService(
        repository=RedisMVPRepository(
            Redis(),
            prefix="mvp",
        )
    )


def test_match_squad_blocks_injured_player():
    service = build()
    service.create_club(
        club_id="c1",
        name="Club",
        country="TR",
        now=100,
    )
    service.create_player(
        player_id="p1",
        club_id="c1",
        name="Player",
        position="ST",
        age=22,
        market_value=2,
        now=101,
    )
    service.create_match(
        match_id="m1",
        club_id="c1",
        opponent="Opponent",
        competition="League",
        kickoff_at=300,
        venue="HOME",
        now=102,
    )
    service.set_player_availability(
        club_id="c1",
        player_id="p1",
        availability="INJURED",
        note="Hamstring",
    )

    with pytest.raises(MVPValidationError):
        service.set_match_squad(
            match_id="m1",
            club_id="c1",
            player_ids=("p1",),
            now=103,
        )
