import os
import pytest

from apps.api.app.production_readiness import (
    ConfigurationValidationError,
    MaintenanceController,
    OperationalCertification,
    ProductionReadinessValidator,
    ReadinessCheck,
)


def test_configuration_validation_rejects_missing_required(monkeypatch):
    monkeypatch.delenv("REQUIRED_VALUE", raising=False)
    validator = ProductionReadinessValidator(
        environment="production",
        required_variables=("REQUIRED_VALUE",),
    )

    report = validator.build_report(now=100)

    assert report.ready is False
    assert any(
        item.name == "config:REQUIRED_VALUE"
        and item.ok is False
        for item in report.checks
    )


def test_require_ready_raises_for_failed_critical_check(monkeypatch):
    monkeypatch.setenv(
        "AUTH_TOKEN_SECRET",
        "a-valid-secret-value",
    )
    monkeypatch.setenv(
        "PROVIDER_API_KEYS",
        "provider:key",
    )
    validator = ProductionReadinessValidator(
        environment="production",
    )

    with pytest.raises(ConfigurationValidationError):
        validator.require_ready(
            runtime_checks=(
                ReadinessCheck(
                    name="database",
                    ok=False,
                    critical=True,
                    detail="offline",
                ),
            )
        )


def test_maintenance_mode_blocks_certification(monkeypatch):
    monkeypatch.setenv(
        "AUTH_TOKEN_SECRET",
        "a-valid-secret-value",
    )
    monkeypatch.setenv(
        "PROVIDER_API_KEYS",
        "provider:key",
    )
    maintenance = MaintenanceController()
    maintenance.enable(
        reason="database migration",
        owner="ops",
        now=100,
    )
    certification = OperationalCertification(
        readiness_validator=ProductionReadinessValidator(
            environment="production",
        ),
        maintenance_controller=maintenance,
    )

    report = certification.generate(now=101)

    assert report["certified"] is False
    assert report["maintenance"]["enabled"] is True


def test_configuration_fingerprint_is_stable(monkeypatch):
    monkeypatch.setenv(
        "AUTH_TOKEN_SECRET",
        "a-valid-secret-value",
    )
    validator = ProductionReadinessValidator(
        environment="test",
    )

    first = validator.build_report(now=100)
    second = validator.build_report(now=200)

    assert (
        first.configuration_fingerprint
        == second.configuration_fingerprint
    )
