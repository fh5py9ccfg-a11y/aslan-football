from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time


@dataclass(frozen=True)
class AcceptanceCheck:
    name: str
    passed: bool
    severity: str
    details: str


@dataclass(frozen=True)
class PilotAcceptanceReport:
    report_id: str
    club_id: str
    build_version: str
    checks: tuple[dict, ...]
    passed_checks: int
    failed_checks: int
    critical_failures: int
    acceptance_score: float
    status: str
    fingerprint: str
    generated_at: int


class PilotAcceptanceService:
    def __init__(
        self,
        *,
        final_pilot_service,
        stabilization_service,
        observability_service,
        intelligence_service,
    ):
        self.final_pilot_service = final_pilot_service
        self.stabilization_service = stabilization_service
        self.observability_service = observability_service
        self.intelligence_service = intelligence_service

    def run_acceptance(
        self,
        *,
        report_id: str,
        club_id: str,
        reviewer: str = "acceptance-bot",
        now: int | None = None,
    ) -> PilotAcceptanceReport:
        current = int(now if now is not None else time.time())

        final = self.final_pilot_service.run_final_pilot(
            report_id=f"{report_id}:final",
            club_id=club_id,
            reviewer=reviewer,
            now=current,
        )
        security = self.stabilization_service.security_report(
            report_id=f"{report_id}:security",
            environment="production",
            now=current,
        )
        backup = self.stabilization_service.create_backup(
            backup_id=f"{report_id}:backup",
            club_id=club_id,
            now=current,
        )
        restore = self.stabilization_service.validate_restore(
            validation_id=f"{report_id}:restore",
            backup_id=backup.backup_id,
            payload_json=backup.payload_json,
            expected_checksum=backup.checksum,
            now=current,
        )
        health = self.observability_service.health_score(
            report_id=f"{report_id}:health",
            club_id=club_id,
            now=current,
        )
        models = self.intelligence_service.repository.list_models(
            club_id
        )
        active_models = [
            item for item in models
            if item.status == "ACTIVE"
        ]
        predictions = self.intelligence_service.repository.list_predictions(
            club_id
        )
        pipeline_runs = (
            self.intelligence_service.repository
            .list_pipeline_runs(club_id)
        )

        checks = (
            AcceptanceCheck(
                name="final_pilot_ready",
                passed=final.final_status == "READY",
                severity="CRITICAL",
                details=final.final_status,
            ),
            AcceptanceCheck(
                name="security_production_ready",
                passed=security.production_ready,
                severity="CRITICAL",
                details="; ".join(security.blockers) or "ok",
            ),
            AcceptanceCheck(
                name="backup_restore_valid",
                passed=restore.restorable,
                severity="CRITICAL",
                details="; ".join(restore.errors) or "ok",
            ),
            AcceptanceCheck(
                name="system_health",
                passed=health.status != "UNHEALTHY",
                severity="CRITICAL",
                details=f"{health.status} / {health.health_score}",
            ),
            AcceptanceCheck(
                name="active_model",
                passed=bool(active_models),
                severity="CRITICAL",
                details=(
                    active_models[0].model_version
                    if active_models else "missing"
                ),
            ),
            AcceptanceCheck(
                name="prediction_created",
                passed=bool(predictions),
                severity="MAJOR",
                details=str(len(predictions)),
            ),
            AcceptanceCheck(
                name="pipeline_executed",
                passed=bool(pipeline_runs),
                severity="MAJOR",
                details=str(len(pipeline_runs)),
            ),
            AcceptanceCheck(
                name="release_gate",
                passed=final.release_gate_status != "NO_GO",
                severity="CRITICAL",
                details=final.release_gate_status,
            ),
            AcceptanceCheck(
                name="pilot_readiness",
                passed=final.pilot_readiness_status == "READY",
                severity="MAJOR",
                details=final.pilot_readiness_status,
            ),
        )

        passed = sum(1 for item in checks if item.passed)
        failed = len(checks) - passed
        critical_failures = sum(
            1 for item in checks
            if not item.passed and item.severity == "CRITICAL"
        )
        score = passed / len(checks) * 100
        status = (
            "ACCEPTED"
            if critical_failures == 0 and score >= 90
            else "CONDITIONAL"
            if critical_failures == 0 and score >= 75
            else "REJECTED"
        )

        serialized_checks = tuple(
            item.__dict__
            for item in checks
        )
        fingerprint_payload = {
            "club_id": club_id,
            "build_version": "build-021",
            "checks": serialized_checks,
            "status": status,
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_payload,
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        return PilotAcceptanceReport(
            report_id=report_id,
            club_id=club_id,
            build_version="build-021",
            checks=serialized_checks,
            passed_checks=passed,
            failed_checks=failed,
            critical_failures=critical_failures,
            acceptance_score=round(score, 2),
            status=status,
            fingerprint=fingerprint,
            generated_at=current,
        )

    def repeatability_check(
        self,
        *,
        club_id: str,
        now: int | None = None,
    ) -> dict:
        first = self.final_pilot_service.seed_final_demo(
            club_id=club_id,
            now=now,
        )
        second = self.final_pilot_service.seed_final_demo(
            club_id=club_id,
            now=now,
        )
        stable = (
            first["players"] == second["players"]
            and first["matches"] == second["matches"]
            and first["club_profile_id"] == second["club_profile_id"]
            and first["opponent_profile_id"] == second["opponent_profile_id"]
        )
        return {
            "club_id": club_id,
            "stable": stable,
            "first": first,
            "second": second,
        }
