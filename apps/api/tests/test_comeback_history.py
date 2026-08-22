from app.comeback_history import TeamComebackProfile


def test_team_profile_rates_are_calculated_safely():
    profile = TeamComebackProfile(
        team="A",
        matches=20,
        halftime_behind=5,
        halftime_behind_wins=2,
        halftime_ahead=8,
        halftime_ahead_losses=1,
        goals_scored=30,
        second_half_goals_scored=18,
        home_2_1_matches=2,
        away_1_2_matches=0,
    )

    assert profile.comeback_rate_when_behind == 0.4
    assert profile.loss_rate_when_ahead == 0.125
    assert profile.second_half_goal_share == 0.6
    assert profile.home_2_1_rate == 0.1
    assert profile.away_1_2_rate == 0.0


def test_team_profile_defaults_do_not_invent_history():
    profile = TeamComebackProfile(
        team="B",
        matches=0,
        halftime_behind=0,
        halftime_behind_wins=0,
        halftime_ahead=0,
        halftime_ahead_losses=0,
        goals_scored=0,
        second_half_goals_scored=0,
        home_2_1_matches=0,
        away_1_2_matches=0,
    )

    assert profile.comeback_rate_when_behind == 0.0
    assert profile.loss_rate_when_ahead == 0.0
    assert profile.second_half_goal_share == 0.5
