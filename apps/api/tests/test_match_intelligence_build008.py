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
    positions = (
        "GK", "RB", "CB", "CB", "LB",
        "DM", "CM", "AM", "RW", "LW", "ST",
        "ST", "CM",
    )
    for index, position in enumerate(positions, start=1):
        workspace.create_player(
            player_id=f"p{index}",
            club_id="c1",
            name=f"Oyuncu {index}",
            position=position,
            age=21 + index % 7,
            market_value=2 + index * 0.4,
            now=100,
        )
    workspace.create_match(
        match_id="m1",
        club_id="c1",
        opponent="Rakip",
        competition="Lig",
        kickoff_at=300,
        venue="HOME",
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
    prediction = service.predict(
        prediction_id="pred1",
        club_id="c1",
        match_id="m1",
        club_profile_id="club",
        opponent_profile_id="opp",
        now=101,
    )
    return service, prediction


def test_lineup_and_tactical_reports():
    service, _ = build()
    lineup = service.lineup_impact_report(
        report_id="line1",
        club_id="c1",
        match_id="m1",
        selected_player_ids=tuple(
            f"p{i}" for i in range(1, 12)
        ),
        now=102,
    )
    tactical = service.tactical_matchup(
        matchup_id="t1",
        club_id="c1",
        match_id="m1",
        own_style="HIGH_PRESS",
        opponent_style="POSSESSION",
        now=102,
    )

    assert lineup.starter_strength > 0
    assert 0 <= lineup.cohesion_score <= 100
    assert tactical.transition_modifier > 0
    assert len(tactical.notes) >= 2


def test_monte_carlo_probabilities():
    service, prediction = build()
    lineup = service.lineup_impact_report(
        report_id="line1",
        club_id="c1",
        match_id="m1",
        selected_player_ids=tuple(
            f"p{i}" for i in range(1, 12)
        ),
        now=102,
    )
    tactical = service.tactical_matchup(
        matchup_id="t1",
        club_id="c1",
        match_id="m1",
        own_style="TRANSITION",
        opponent_style="POSSESSION",
        now=102,
    )
    simulation = service.monte_carlo_simulation(
        simulation_id="sim1",
        prediction_id=prediction.prediction_id,
        iterations=5000,
        lineup_report_id=lineup.report_id,
        tactical_matchup_id=tactical.matchup_id,
        now=103,
    )

    total = (
        simulation.home_win_probability
        + simulation.draw_probability
        + simulation.away_win_probability
    )
    assert 99.9 <= total <= 100.1
    assert len(simulation.score_distribution) == 10
    assert 0 <= simulation.over_2_5_probability <= 100
    assert 0 <= simulation.both_teams_score_probability <= 100
