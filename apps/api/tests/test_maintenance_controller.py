from apps.api.app.production_readiness import (
    MaintenanceController,
)


def test_maintenance_controller_lifecycle():
    controller = MaintenanceController()

    enabled = controller.enable(
        reason="upgrade",
        owner="ops-user",
        now=100,
    )

    assert enabled.enabled is True
    assert enabled.owner == "ops-user"

    disabled = controller.disable()

    assert disabled.enabled is False
    assert disabled.reason is None
