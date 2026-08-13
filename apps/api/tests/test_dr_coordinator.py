from apps.api.app.dr_coordinator import (
    DisasterRecoveryCoordinator,
)

class Checkpoint:
    rpo_seconds = 10
    updated_at = 90

class Repository:
    max_rpo_seconds = 30

    def get_checkpoint(self, region):
        return Checkpoint()

def test_recovery_objectives_are_evaluated():
    coordinator = DisasterRecoveryCoordinator(
        repository=Repository(),
        max_rto_seconds=300,
    )
    result = coordinator.evaluate(
        "eu-west",
        now=100,
    )
    assert result.healthy is True
    assert result.rpo_seconds == 10
    assert result.estimated_rto_seconds == 40
