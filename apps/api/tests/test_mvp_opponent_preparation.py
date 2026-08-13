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


def test_opponent_profile_and_match_preparation():
    service = build()
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
    opponent = service.save_opponent_profile(
        opponent_id="o1",
        club_id="c1",
        name="Opponent",
        formation="4-3-3",
        strengths=("Transitions",),
        weaknesses=("Set pieces",),
        key_players=("Number 10",),
        notes="Aggressive press",
        now=102,
    )
    preparation = service.create_match_preparation(
        preparation_id="prep1",
        match_id="m1",
        club_id="c1",
        opponent_id="o1",
        tactical_plan="Control central spaces",
        pressing_plan="Mid block",
        set_piece_plan="Near-post run",
        objectives=("Win second balls",),
        now=103,
    )
    ready = service.transition_preparation(
        preparation_id="prep1",
        target_status="READY",
        now=104,
    )
    dashboard = service.dashboard(
        club_id="c1"
    )

    assert opponent.formation == "4-3-3"
    assert preparation.status == "DRAFT"
    assert ready.status == "READY"
    assert dashboard["matches"][0]["preparations"][0]["status"] == "READY"
    assert dashboard["opponents"][0]["name"] == "Opponent"
