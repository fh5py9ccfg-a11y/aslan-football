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

    def delete(self, key):
        self.values.pop(key, None)

    def srem(self, key, value):
        self.sets.setdefault(key, set()).discard(value)


def build():
    return MVPWorkspaceService(
        repository=RedisMVPRepository(
            Redis(),
            prefix="mvp",
        )
    )


def test_player_update_and_delete():
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
        name="Old Name",
        position="CM",
        age=20,
        market_value=1.0,
        now=101,
    )

    updated = service.update_player(
        player_id="p1",
        club_id="c1",
        name="New Name",
        position="AM",
        age=21,
        market_value=2.5,
    )
    service.delete_player(
        player_id="p1",
        club_id="c1",
    )

    assert updated.name == "New Name"
    assert updated.position == "AM"
    assert service.repository.list_players("c1") == ()


def test_demo_seed_is_idempotent():
    service = build()

    first = service.seed_demo(now=1000)
    second = service.seed_demo(now=1001)

    assert first["summary"]["player_count"] == 5
    assert second["summary"]["player_count"] == 5
    assert second["summary"]["completed_matches"] == 1
