from apps.api.app.mvp_workspace import (
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


def setup(service):
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


def test_performance_and_player_form():
    service = build()
    setup(service)

    service.record_player_performance(
        match_id="m1",
        club_id="c1",
        player_id="p1",
        minutes=90,
        goals=1,
        assists=1,
        rating=8.2,
        note="Strong game",
        now=103,
    )
    rows = service.player_form(
        club_id="c1"
    )

    assert rows[0]["matches"] == 1
    assert rows[0]["goals"] == 1
    assert rows[0]["assists"] == 1
    assert rows[0]["average_rating"] == 8.2
