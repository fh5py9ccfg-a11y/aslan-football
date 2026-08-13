from apps.api.app.ensemble_training import (
    EnsembleTrainingService,
)


def sample_csv(rows: int = 40) -> str:
    header = (
        "match_id,competition,season,kickoff_at,"
        "home_team,away_team,home_goals,away_goals,"
        "home_xg,away_xg,home_elo,away_elo\n"
    )
    lines = []
    for index in range(rows):
        home_goals = (index * 2) % 4
        away_goals = (index + 1) % 3
        lines.append(
            f"m{index},Pilot Lig,2025-26,{1000 + index},"
            f"Ev {index},Dep {index},{home_goals},{away_goals},"
            f"{1.0 + (index % 5) * 0.2},{0.8 + (index % 4) * 0.2},"
            f"{1480 + index * 4},{1510 + index * 2}"
        )
    return header + "\n".join(lines) + "\n"


def test_train_ensemble_and_predict():
    service = EnsembleTrainingService()
    model = service.train(
        model_id="ens1",
        csv_text=sample_csv(),
        competition="Pilot Lig",
        validation_fraction=0.25,
        now=100,
    )
    prediction = service.predict(
        model=model,
        home_xg=1.7,
        away_xg=1.0,
        home_elo=1580,
        away_elo=1500,
        home_form=0.7,
        away_form=0.4,
    )

    assert model.training_matches >= 20
    assert model.validation_matches >= 5
    assert 0 <= model.validation_accuracy <= 100
    assert abs(
        prediction["home_probability"]
        + prediction["draw_probability"]
        + prediction["away_probability"]
        - 100
    ) < 0.1
    assert prediction["recommended_result"] in {
        "HOME", "DRAW", "AWAY",
    }


def test_walk_forward_ensemble():
    service = EnsembleTrainingService()
    report = service.walk_forward_backtest(
        report_id="wf1",
        csv_text=sample_csv(50),
        competition="Pilot Lig",
        minimum_train_size=25,
        step_size=5,
        now=100,
    )

    assert report.folds == 5
    assert report.evaluated_matches == 25
    assert 0 <= report.accuracy <= 100
    assert report.mean_log_loss >= 0
    assert report.mean_brier_score >= 0
