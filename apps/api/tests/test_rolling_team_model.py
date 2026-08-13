from apps.api.app.rolling_team_model import (
    RollingTeamModelService,
)


def league_csv(rounds: int = 24) -> str:
    teams = ["A", "B", "C", "D", "E", "F"]
    header = (
        "match_id,competition,season,kickoff_at,"
        "home_team,away_team,home_goals,away_goals,"
        "home_xg,away_xg,home_elo,away_elo\n"
    )
    lines = []
    index = 0
    for round_no in range(rounds):
        for pair in range(3):
            home = teams[(pair * 2 + round_no) % len(teams)]
            away = teams[(pair * 2 + 1 + round_no) % len(teams)]
            home_goals = (round_no + pair) % 4
            away_goals = (round_no + pair + 1) % 3
            lines.append(
                f"m{index},Pilot Lig,2025-26,{1000 + index},"
                f"{home},{away},{home_goals},{away_goals},"
                f"{1.1 + (index % 5)*0.2},{0.8 + (index % 4)*0.2},"
                f"{1500 + (index % 6)*12},{1490 + (index % 5)*10}"
            )
            index += 1
    return header + "\n".join(lines) + "\n"


def test_build_rows_is_leakage_safe_and_trainable():
    service = RollingTeamModelService()
    rows = service.build_rows(
        csv_text=league_csv(),
        competition="Pilot Lig",
    )
    model = service.train(
        model_id="rolling1",
        csv_text=league_csv(),
        competition="Pilot Lig",
        validation_fraction=0.25,
        epochs=150,
        now=100,
    )

    assert len(rows) >= 12
    assert rows[0].kickoff_at > 1000
    assert model.training_rows >= 9
    assert model.validation_rows >= 3
    assert 0 <= model.validation_accuracy <= 100
    assert model.validation_log_loss >= 0


def test_predict_from_features():
    service = RollingTeamModelService()
    model = service.train(
        model_id="rolling1",
        csv_text=league_csv(),
        competition="Pilot Lig",
        epochs=150,
        now=100,
    )
    prediction = service.predict_from_features(
        model=model,
        features=(
            1.7,
            1.0,
            0.20,
            0.70,
            0.40,
            0.50,
            -0.20,
            0.35,
            -0.10,
            12.0,
            12.0,
        ),
    )

    assert abs(
        prediction["home_probability"]
        + prediction["draw_probability"]
        + prediction["away_probability"]
        - 100
    ) < 0.1
    assert prediction["recommended_result"] in {
        "HOME", "DRAW", "AWAY",
    }
