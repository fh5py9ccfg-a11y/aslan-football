from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import time


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    ok: bool
    critical: bool
    detail: str


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    environment: str
    generated_at: int
    configuration_fingerprint: str
    checks: tuple[ReadinessCheck, ...]


class ConfigurationValidationError(RuntimeError):
    pass


class ProductionReadinessValidator:
    def __init__(
        self,
        *,
        environment: str,
        required_variables: tuple[str, ...] = (),
        minimum_secret_length: int = 16,
    ):
        self.environment = environment
        self.required_variables = required_variables
        self.minimum_secret_length = minimum_secret_length

    def validate_configuration(self) -> tuple[ReadinessCheck, ...]:
        checks = []

        for variable in self.required_variables:
            value = os.getenv(variable, "")
            checks.append(
                ReadinessCheck(
                    name=f"config:{variable}",
                    ok=bool(value),
                    critical=True,
                    detail=(
                        "configured"
                        if value
                        else "missing"
                    ),
                )
            )

        secret = os.getenv("AUTH_TOKEN_SECRET", "")
        checks.append(
            ReadinessCheck(
                name="security:auth-token-secret",
                ok=(
                    self.environment in {"test", "development"}
                    or len(secret) >= self.minimum_secret_length
                ),
                critical=True,
                detail=(
                    "valid"
                    if len(secret) >= self.minimum_secret_length
                    else "too-short-or-missing"
                ),
            )
        )

        production_defaults_ok = not (
            self.environment == "production"
            and os.getenv("PROVIDER_API_KEYS", "").strip() == ""
        )
        checks.append(
            ReadinessCheck(
                name="security:provider-api-keys",
                ok=production_defaults_ok,
                critical=True,
                detail=(
                    "configured"
                    if production_defaults_ok
                    else "required-in-production"
                ),
            )
        )

        return tuple(checks)

    def build_report(
        self,
        *,
        runtime_checks: tuple[ReadinessCheck, ...] = (),
        now: int | None = None,
    ) -> ReadinessReport:
        current = int(now if now is not None else time.time())
        checks = self.validate_configuration() + runtime_checks
        ready = all(
            check.ok
            for check in checks
            if check.critical
        )

        fingerprint_payload = {
            "environment": self.environment,
            "required_variables": self.required_variables,
            "checks": [
                {
                    "name": item.name,
                    "ok": item.ok,
                    "critical": item.critical,
                }
                for item in checks
            ],
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        return ReadinessReport(
            ready=ready,
            environment=self.environment,
            generated_at=current,
            configuration_fingerprint=fingerprint,
            checks=checks,
        )

    def require_ready(
        self,
        *,
        runtime_checks: tuple[ReadinessCheck, ...] = (),
    ) -> ReadinessReport:
        report = self.build_report(
            runtime_checks=runtime_checks
        )
        if not report.ready:
            failures = ", ".join(
                item.name
                for item in report.checks
                if item.critical and not item.ok
            )
            raise ConfigurationValidationError(
                f"Production readiness başarısız: {failures}"
            )
        return report


@dataclass(frozen=True)
class MaintenanceState:
    enabled: bool
    reason: str | None
    started_at: int | None
    owner: str | None


class MaintenanceController:
    def __init__(self):
        self.enabled = False
        self.reason = None
        self.started_at = None
        self.owner = None

    def enable(
        self,
        *,
        reason: str,
        owner: str,
        now: int | None = None,
    ) -> MaintenanceState:
        self.enabled = True
        self.reason = reason[:500]
        self.owner = owner[:200]
        self.started_at = int(
            now if now is not None else time.time()
        )
        return self.snapshot()

    def disable(self) -> MaintenanceState:
        self.enabled = False
        self.reason = None
        self.owner = None
        self.started_at = None
        return self.snapshot()

    def snapshot(self) -> MaintenanceState:
        return MaintenanceState(
            enabled=self.enabled,
            reason=self.reason,
            started_at=self.started_at,
            owner=self.owner,
        )


class OperationalCertification:
    def __init__(
        self,
        *,
        readiness_validator,
        maintenance_controller,
        self_healing_orchestrator=None,
        dr_repository=None,
    ):
        self.readiness_validator = readiness_validator
        self.maintenance_controller = maintenance_controller
        self.self_healing_orchestrator = self_healing_orchestrator
        self.dr_repository = dr_repository

    def generate(self, *, now: int | None = None) -> dict:
        runtime_checks = []

        maintenance = self.maintenance_controller.snapshot()
        runtime_checks.append(
            ReadinessCheck(
                name="runtime:maintenance-mode",
                ok=not maintenance.enabled,
                critical=True,
                detail=(
                    "disabled"
                    if not maintenance.enabled
                    else maintenance.reason or "enabled"
                ),
            )
        )

        if self.self_healing_orchestrator is not None:
            cluster = self.self_healing_orchestrator.cluster_health()
            runtime_checks.append(
                ReadinessCheck(
                    name="runtime:self-healing",
                    ok=bool(cluster.get("ready")),
                    critical=False,
                    detail=json.dumps(
                        cluster,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                )
            )

        if self.dr_repository is not None:
            dr_health = self.dr_repository.health()
            runtime_checks.append(
                ReadinessCheck(
                    name="runtime:disaster-recovery",
                    ok=bool(dr_health.get("rpo_within_target")),
                    critical=False,
                    detail=json.dumps(
                        dr_health,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                )
            )

        report = self.readiness_validator.build_report(
            runtime_checks=tuple(runtime_checks),
            now=now,
        )

        return {
            "certified": report.ready,
            "generated_at": report.generated_at,
            "environment": report.environment,
            "configuration_fingerprint": (
                report.configuration_fingerprint
            ),
            "maintenance": maintenance.__dict__,
            "checks": [
                item.__dict__
                for item in report.checks
            ],
        }
