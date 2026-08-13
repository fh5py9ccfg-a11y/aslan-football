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


def test_club_player_match_dashboard():
    service = build()
    service.create_club(
        club_id="aslan",
        name="Aslan Spor",
        country="Türkiye",
        now=100,
    )
    service.create_player(
        player_id="p1",
        club_id="aslan",
        name="Ali Yılmaz",
        position="ST",
        age=23,
        market_value=4.5,
        now=101,
    )
    service.create_match(
        match_id="m1",
        club_id="aslan",
        opponent="Rakip FK",
        competition="Lig",
        kickoff_at=200,
        venue="HOME",
        now=102,
    )
    service.complete_match(
        match_id="m1",
        club_id="aslan",
        goals_for=2,
        goals_against=1,
    )

    dashboard = service.dashboard(
        club_id="aslan"
    )

    assert dashboard["summary"]["player_count"] == 1
    assert dashboard["summary"]["squad_value"] == 4.5
    assert dashboard["summary"]["wins"] == 1


def test_player_requires_existing_club():
    service = build()
    try:
        service.create_player(
            player_id="p1",
            club_id="missing",
            name="Ali",
            position="ST",
            age=22,
            market_value=1,
        )
    except KeyError:
        pass
    else:
        raise AssertionError("KeyError bekleniyordu")
