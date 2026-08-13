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


def test_match_report_appears_in_dashboard():
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
    report = service.save_match_report(
        match_id="m1",
        club_id="c1",
        summary="Controlled match throughout",
        positives="Pressing",
        improvements="Finishing",
        now=102,
    )
    dashboard = service.dashboard(
        club_id="c1"
    )

    assert report.positives == "Pressing"
    assert dashboard["matches"][0]["report"]["summary"] == (
        "Controlled match throughout"
    )
