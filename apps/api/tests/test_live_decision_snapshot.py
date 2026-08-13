from apps.api.app.live_decision_orchestrator import (
    LiveDecisionOrchestrator,
)


class Snapshot:
    home_xg = 1.1
    away_xg = 0.7
    home_momentum = 4.2
    away_momentum = 1.0
    possession_trend = 6.0
    anomaly_score = 2.3
    event_count = 18


def test_streaming_snapshot_is_converted_to_features():
    features = (
        LiveDecisionOrchestrator
        .snapshot_from_streaming(Snapshot())
    )

    assert features["home_xg"] == 1.1
    assert features["event_count"] == 18
    assert features["anomaly_score"] == 2.3
