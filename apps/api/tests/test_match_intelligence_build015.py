from apps.api.app.match_intelligence import (
    MatchIntelligenceService,
    RedisMatchIntelligenceRepository,
)
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
    redis = Redis()
    workspace = MVPWorkspaceService(
        repository=RedisMVPRepository(
            redis,
            prefix="mvp",
        )
    )
    workspace.create_club(
        club_id="c1",
        name="Aslan",
        country="TR",
        now=100,
    )
    positions = (
        "GK", "RB", "CB", "CB", "LB",
        "DM", "CM", "AM", "RW", "LW", "ST",
        "GK", "CB", "CM", "ST", "RW", "LB", "DM",
    )
    for index, position in enumerate(positions, start=1):
        workspace.create_player(
            player_id=f"p{index}",
            club_id="c1",
            name=f"Oyuncu {index}",
            position=position,
            age=21 + index % 8,
            market_value=2 + index * 0.2,
            now=100,
        )
    for index in range(1, 4):
        workspace.create_match(
            match_id=f"m{index}",
            club_id="c1",
            opponent=f"Rakip {index}",
            competition="Lig",
            kickoff_at=200 + index,
            venue="HOME" if index % 2 else "AWAY",
            now=100,
        )

    service = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intel",
        ),
        workspace_service=workspace,
    )
    for profile_id, name, elo in (
        ("club", "Aslan", 1580),
        ("opp", "Rakip", 1500),
    ):
        service.save_opponent_profile(
            profile_id=profile_id,
            club_id="c1",
            team_name=name,
            attack_rating=1.05,
            defence_rating=0.98,
            form_rating=0.60,
            home_rating=0.65,
            away_rating=0.45,
            goals_for_average=1.45,
            goals_against_average=1.15,
            sample_size=12,
            elo_rating=elo,
            xg_for_average=1.4,
            xg_against_average=1.1,
            now=100,
        )
    service.register_model(
        model_id="model1",
        club_id="c1",
        model_version="build-015",
        competition="ALL",
        feature_set=("elo", "xg", "form"),
        training_sample_size=100,
        validation_brier_score=0.55,
        validation_log_loss=1.0,
        status="ACTIVE",
        now=100,
    )
    return service


def test_end_to_end_pipeline_and_release_gate():
    service = build()
    run = service.run_end_to_end_pipeline(
        run_id="run1",
        club_id="c1",
        match_id="m1",
        club_profile_id="club",
        opponent_profile_id="opp",
        reviewer="coach",
        now=101,
    )
    gate = service.release_gate(
        gate_id="gate2",
        club_id="c1",
        tests_passed=True,
        documentation_ready=True,
        now=102,
    )

    assert run.prediction_id == "run1:prediction"
    assert run.approval_status in {
        "APPROVED",
        "NEEDS_REVIEW",
    }
    assert gate.overall_status in {
        "GO",
        "CONDITIONAL_GO",
        "NO_GO",
    }


def test_pilot_readiness():
    service = build()
    service.run_end_to_end_pipeline(
        run_id="run1",
        club_id="c1",
        match_id="m1",
        club_profile_id="club",
        opponent_profile_id="opp",
        reviewer="coach",
        now=101,
    )
    report = service.pilot_readiness(
        report_id="pilot1",
        club_id="c1",
        documentation_ready=True,
        now=102,
    )

    assert report.status == "READY"
    assert report.operational_score >= 90
    assert len(report.action_items) >= 1
