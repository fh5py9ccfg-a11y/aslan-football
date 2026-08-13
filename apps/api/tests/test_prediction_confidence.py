from apps.api.app.prediction_confidence import (
    PredictionConfidenceAdjuster,
)


def test_low_quality_reduces_confidence():
    adjuster = PredictionConfidenceAdjuster()

    high = adjuster.adjust(
        base_confidence=0.9,
        provider_trust=100,
        data_quality=100,
    )
    low = adjuster.adjust(
        base_confidence=0.9,
        provider_trust=40,
        data_quality=50,
    )

    assert high.adjusted_confidence == 0.9
    assert low.adjusted_confidence < high.adjusted_confidence
