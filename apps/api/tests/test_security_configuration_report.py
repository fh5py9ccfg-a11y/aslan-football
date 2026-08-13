import os

from apps.api.app.pilot_stabilization import (
    PilotStabilizationService,
)


class Dummy:
    pass


def test_production_default_secret_is_blocked(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "MVP_AUTH_SECRET",
        "local-pilot-secret-change-me",
    )
    monkeypatch.setenv(
        "MVP_AUTH_TTL_SECONDS",
        "86400",
    )
    monkeypatch.setenv(
        "MVP_AUTH_PREFIX",
        "aslan:mvp-auth",
    )
    service = PilotStabilizationService(
        workspace_service=Dummy(),
        intelligence_service=Dummy(),
    )

    report = service.security_report(
        report_id="r1",
        environment="production",
        now=100,
    )

    assert report.production_ready is False
    assert len(report.blockers) >= 1
