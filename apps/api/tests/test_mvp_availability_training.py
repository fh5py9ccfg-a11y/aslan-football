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


def test_availability_and_training_attendance():
    service = build()
    setup(service)

    updated = service.set_player_availability(
        club_id="c1",
        player_id="p1",
        availability="doubtful",
        note="Minor knock",
    )
    session = service.create_training(
        session_id="t1",
        club_id="c1",
        title="Tactical session",
        starts_at=200,
        focus="Pressing",
        now=102,
    )
    attendance = service.record_attendance(
        session_id="t1",
        player_id="p1",
        status="limited",
        note="Individual work",
        now=103,
    )
    dashboard = service.dashboard(
        club_id="c1"
    )

    assert updated.availability == "DOUBTFUL"
    assert session.focus == "Pressing"
    assert attendance.status == "LIMITED"
    assert dashboard["summary"]["unavailable_players"] == 1
    assert len(dashboard["trainings"]) == 1
