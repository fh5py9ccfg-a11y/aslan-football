import pytest

from apps.api.app.real_data_training import (
    RealDataTrainingService,
    RealDataValidationError,
)


def sample_csv(rows: int = 20) -> str:
    header = (
        "match_id,competition,season,kickoff_at,"
        "home_team,away_team,home_goals,away_goals,"
        "home_xg,away_xg,home_elo,away_elo\n"
    )
    lines = []
    for index in range(rows):
        home_goals = index % 4
        away_goals = (index + 1) % 3
        lines.append(
            f"m{index},Pilot Lig,2025-26,{1000 + index},"
            f"Ev {index},Dep {index},{home_goals},{away_goals},"
            f"{1.1 + index % 3 * 0.2},{0.9 + index % 2 * 0.2},"
            f"{1500 + index * 3},{1490 + index * 2}"
        )
    return header + "\n".join(lines) + "\n"


def test_dataset_report():
    service = RealDataTrainingService()
    report = service.dataset_report(
        report_id="r1",
        csv_text=sample_csv(),
        competition="Pilot Lig",
        season="2025-26",
        now=100,
    )

    assert report.valid_rows == 20
    assert report.invalid_rows == 0
    assert sum(report.label_distribution.values()) == 20
    assert len(report.checksum) == 64


def test_train_baseline_and_predict():
    service = RealDataTrainingService()
    model = service.train_baseline(
        model_id="model1",
        csv_text=sample_csv(24),
        competition="Pilot Lig",
        validation_fraction=0.25,
        now=100,
    )
    prediction = service.predict_with_baseline(
        model=model,
        home_xg=1.6,
        away_xg=1.1,
        home_elo=1570,
        away_elo=1500,
    )

    assert model.sample_size == 24
    assert 0 <= model.validation_accuracy <= 100
    assert model.validation_brier_score >= 0
    assert abs(
        prediction["home_probability"]
        + prediction["draw_probability"]
        + prediction["away_probability"]
        - 100
    ) < 0.1


def test_too_few_matches_rejected():
    service = RealDataTrainingService()

    with pytest.raises(RealDataValidationError):
        service.train_baseline(
            model_id="model1",
            csv_text=sample_csv(8),
            competition="Pilot Lig",
            now=100,
        )
