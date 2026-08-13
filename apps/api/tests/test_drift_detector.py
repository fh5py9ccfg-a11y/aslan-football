from apps.api.app.model_monitoring import DriftDetector


def test_identical_distributions_have_zero_psi():
    values = (0.1, 0.2, 0.3, 0.4)

    score = DriftDetector.population_stability_index(
        values,
        values,
    )

    assert score == 0.0


def test_severity_levels():
    assert DriftDetector.severity(
        0.1,
        medium=0.2,
        high=0.5,
        critical=1.0,
    ) == "LOW"
    assert DriftDetector.severity(
        0.7,
        medium=0.2,
        high=0.5,
        critical=1.0,
    ) == "HIGH"
