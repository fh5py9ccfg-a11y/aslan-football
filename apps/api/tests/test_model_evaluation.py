from apps.api.app.model_evaluation import (
    ModelEvaluator,
    ProbabilityCalibrator,
)


def test_model_metrics_are_calculated():
    metrics = ModelEvaluator.evaluate(
        probabilities=(0.9, 0.2, 0.8, 0.1),
        outcomes=(1, 0, 1, 0),
    )

    assert metrics.accuracy == 1.0
    assert metrics.brier_score < 0.05
    assert metrics.log_loss < 0.3


def test_challenger_wins_when_all_gates_pass():
    champion = ModelEvaluator.evaluate(
        probabilities=(0.7, 0.4, 0.6, 0.3),
        outcomes=(1, 0, 1, 0),
    )
    challenger = ModelEvaluator.evaluate(
        probabilities=(0.9, 0.1, 0.85, 0.15),
        outcomes=(1, 0, 1, 0),
    )

    comparison = ModelEvaluator.compare(
        champion_id="champion",
        challenger_id="challenger",
        champion_metrics=champion,
        challenger_metrics=challenger,
    )

    assert comparison.winner == "challenger"


def test_probability_calibration():
    calibrator = ProbabilityCalibrator(
        slope=0.5,
        intercept=0.0,
    )

    calibrated = calibrator.calibrate(0.9)

    assert 0.5 < calibrated < 0.9
