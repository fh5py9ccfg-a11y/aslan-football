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
        repository=RedisMVPRepository(redis, prefix="mvp")
    )
    workspace.create_club(
        club_id="c1",
        name="Aslan",
        country="TR",
        now=100,
    )
    scores = (
        (2, 1), (1, 0), (1, 1), (0, 1),
        (3, 1), (2, 2), (2, 0), (1, 2),
    )
    for index, score in enumerate(scores, start=1):
        workspace.create_match(
            match_id=f"m{index}",
            club_id="c1",
            opponent="Rakip",
            competition="Lig",
            kickoff_at=100 + index,
            venue="HOME" if index % 2 else "AWAY",
            now=100,
        )
        workspace.complete_match(
            match_id=f"m{index}",
            club_id="c1",
            goals_for=score[0],
            goals_against=score[1],
        )
    service = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intel",
        ),
        workspace_service=workspace,
    )
    return service


def test_walk_forward_and_history_profile():
    service = build()
    report = service.walk_forward_backtest(
        report_id="wf1",
        club_id="c1",
        competition="Lig",
        warmup_matches=3,
        now=200,
    )
    profile = service.derive_opponent_profile_from_history(
        profile_id="opp-history",
        club_id="c1",
        opponent_name="Rakip",
        cutoff_at=108,
        now=200,
    )

    assert report.evaluated_matches == 5
    assert report.leakage_checks_passed is True
    assert profile.sample_size == 7


def test_reproducibility_record():
    service = build()
    service.save_opponent_profile(
        profile_id="club",
        club_id="c1",
        team_name="Aslan",
        attack_rating=1.0,
        defence_rating=1.0,
        form_rating=0.5,
        home_rating=0.5,
        away_rating=0.5,
        goals_for_average=1.3,
        goals_against_average=1.3,
        sample_size=8,
        elo_rating=1500,
        xg_for_average=1.2,
        xg_against_average=1.2,
        now=200,
    )
    service.save_opponent_profile(
        profile_id="opp",
        club_id="c1",
        team_name="Rakip",
        attack_rating=1.0,
        defence_rating=1.0,
        form_rating=0.5,
        home_rating=0.5,
        away_rating=0.5,
        goals_for_average=1.3,
        goals_against_average=1.3,
        sample_size=8,
        elo_rating=1500,
        xg_for_average=1.2,
        xg_against_average=1.2,
        now=200,
    )
    prediction = service.predict(
        prediction_id="pred1",
        club_id="c1",
        match_id="m8",
        club_profile_id="club",
        opponent_profile_id="opp",
        now=201,
    )
    record = service.reproducibility_record(
        record_id="rep1",
        prediction_id=prediction.prediction_id,
        now=202,
    )

    assert len(record.input_fingerprint) == 64
    assert len(record.output_fingerprint) == 64
    assert record.deterministic is True
