from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import time


@dataclass(frozen=True)
class ProductionPreflightReport:
    report_id: str
    environment: str
    required_variables: tuple[str, ...]
    missing_variables: tuple[str, ...]
    insecure_variables: tuple[str, ...]
    database_ready: bool
    redis_ready: bool
    backup_ready: bool
    observability_ready: bool
    status: str
    generated_at: int


@dataclass(frozen=True)
class MigrationPreflightReport:
    report_id: str
    source_schema: str
    target_schema: str
    compatible: bool
    destructive_changes: tuple[str, ...]
    warnings: tuple[str, ...]
    status: str
    generated_at: int


@dataclass(frozen=True)
class DisasterRecoveryReport:
    report_id: str
    backup_checksum_valid: bool
    restore_schema_valid: bool
    restore_sections_valid: bool
    smoke_test_ready: bool
    recovery_time_objective_minutes: int
    recovery_point_objective_minutes: int
    status: str
    generated_at: int


@dataclass(frozen=True)
class SignedReleaseManifest:
    manifest_id: str
    build_version: str
    package_checksum: str
    source_manifest_checksum: str
    acceptance_fingerprint: str
    signature: str
    immutable: bool
    created_at: int


class ReleaseFreezeValidationError(ValueError):
    pass


class ReleaseFreezeService:
    REQUIRED_ENV = (
        "APP_ENV",
        "AUTH_TOKEN_SECRET",
        "JWT_ACTIVE_KID",
        "JWT_ISSUER",
        "JWT_AUDIENCE",
        "MVP_AUTH_SECRET",
    )

    def production_preflight(
        self,
        *,
        report_id: str,
        database_ready: bool,
        redis_ready: bool,
        backup_ready: bool,
        observability_ready: bool,
        environment: dict[str, str] | None = None,
        now: int | None = None,
    ) -> ProductionPreflightReport:
        env = environment or dict(os.environ)
        missing = [
            key for key in self.REQUIRED_ENV
            if not env.get(key, "").strip()
        ]
        insecure = []
        for key in (
            "AUTH_TOKEN_SECRET",
            "MVP_AUTH_SECRET",
        ):
            value = env.get(key, "")
            if (
                len(value) < 24
                or "change-me" in value.lower()
                or value.lower() in {
                    "secret",
                    "password",
                    "test",
                }
            ):
                insecure.append(key)

        status = (
            "PASS"
            if (
                not missing
                and not insecure
                and database_ready
                and redis_ready
                and backup_ready
                and observability_ready
            )
            else "FAIL"
        )
        return ProductionPreflightReport(
            report_id=report_id,
            environment=env.get("APP_ENV", "unknown"),
            required_variables=self.REQUIRED_ENV,
            missing_variables=tuple(missing),
            insecure_variables=tuple(insecure),
            database_ready=database_ready,
            redis_ready=redis_ready,
            backup_ready=backup_ready,
            observability_ready=observability_ready,
            status=status,
            generated_at=int(now if now is not None else time.time()),
        )

    def migration_preflight(
        self,
        *,
        report_id: str,
        source_schema: str,
        target_schema: str,
        source_fields: tuple[str, ...],
        target_fields: tuple[str, ...],
        now: int | None = None,
    ) -> MigrationPreflightReport:
        source = set(source_fields)
        target = set(target_fields)
        removed = sorted(source - target)
        added = sorted(target - source)

        destructive = tuple(
            f"Alan kaldırılıyor: {field}"
            for field in removed
        )
        warnings = tuple(
            f"Yeni alan eklenecek: {field}"
            for field in added
        )
        compatible = not destructive
        status = (
            "SAFE"
            if compatible
            else "BLOCKED"
        )
        return MigrationPreflightReport(
            report_id=report_id,
            source_schema=source_schema,
            target_schema=target_schema,
            compatible=compatible,
            destructive_changes=destructive,
            warnings=warnings,
            status=status,
            generated_at=int(now if now is not None else time.time()),
        )

    def disaster_recovery_drill(
        self,
        *,
        report_id: str,
        backup_payload: str,
        expected_checksum: str,
        required_sections: tuple[str, ...],
        recovery_time_objective_minutes: int,
        recovery_point_objective_minutes: int,
        smoke_test_ready: bool,
        now: int | None = None,
    ) -> DisasterRecoveryReport:
        actual_checksum = hashlib.sha256(
            backup_payload.encode("utf-8")
        ).hexdigest()
        checksum_valid = actual_checksum == expected_checksum

        try:
            data = json.loads(backup_payload)
        except json.JSONDecodeError:
            data = {}

        schema_valid = bool(data.get("schema_version"))
        sections_valid = all(
            section in data
            for section in required_sections
        )
        status = (
            "PASS"
            if (
                checksum_valid
                and schema_valid
                and sections_valid
                and smoke_test_ready
                and recovery_time_objective_minutes <= 60
                and recovery_point_objective_minutes <= 1440
            )
            else "FAIL"
        )
        return DisasterRecoveryReport(
            report_id=report_id,
            backup_checksum_valid=checksum_valid,
            restore_schema_valid=schema_valid,
            restore_sections_valid=sections_valid,
            smoke_test_ready=smoke_test_ready,
            recovery_time_objective_minutes=recovery_time_objective_minutes,
            recovery_point_objective_minutes=recovery_point_objective_minutes,
            status=status,
            generated_at=int(now if now is not None else time.time()),
        )

    def sign_release(
        self,
        *,
        manifest_id: str,
        build_version: str,
        package_checksum: str,
        source_manifest_checksum: str,
        acceptance_fingerprint: str,
        signing_key: str,
        now: int | None = None,
    ) -> SignedReleaseManifest:
        if len(signing_key) < 24:
            raise ReleaseFreezeValidationError(
                "Release signing key en az 24 karakter olmalıdır"
            )
        canonical = json.dumps(
            {
                "manifest_id": manifest_id,
                "build_version": build_version,
                "package_checksum": package_checksum,
                "source_manifest_checksum": source_manifest_checksum,
                "acceptance_fingerprint": acceptance_fingerprint,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        signature = hashlib.sha256(
            (signing_key + canonical).encode("utf-8")
        ).hexdigest()
        return SignedReleaseManifest(
            manifest_id=manifest_id,
            build_version=build_version,
            package_checksum=package_checksum,
            source_manifest_checksum=source_manifest_checksum,
            acceptance_fingerprint=acceptance_fingerprint,
            signature=signature,
            immutable=True,
            created_at=int(now if now is not None else time.time()),
        )
