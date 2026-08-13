from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import time


@dataclass(frozen=True)
class SecurityConfigurationReport:
    report_id: str
    environment: str
    secure_secret: bool
    default_demo_secret_disabled: bool
    auth_ttl_valid: bool
    redis_prefix_valid: bool
    production_ready: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class BackupManifest:
    backup_id: str
    club_id: str
    schema_version: str
    entity_counts: dict
    checksum: str
    payload_json: str
    created_at: int


@dataclass(frozen=True)
class RestoreValidationReport:
    validation_id: str
    backup_id: str
    checksum_valid: bool
    schema_valid: bool
    required_sections_valid: bool
    restorable: bool
    errors: tuple[str, ...]
    validated_at: int


@dataclass(frozen=True)
class ContractSnapshot:
    snapshot_id: str
    api_version: str
    routes: tuple[str, ...]
    checksum: str
    created_at: int


class PilotStabilizationError(ValueError):
    pass


class PilotStabilizationService:
    REQUIRED_SECTIONS = (
        "club",
        "players",
        "matches",
        "opponents",
        "predictions",
        "models",
    )

    def __init__(
        self,
        *,
        workspace_service,
        intelligence_service,
    ):
        self.workspace_service = workspace_service
        self.intelligence_service = intelligence_service

    def security_report(
        self,
        *,
        report_id: str,
        environment: str | None = None,
        now: int | None = None,
    ) -> SecurityConfigurationReport:
        env = (
            environment
            or os.getenv("APP_ENV", "development")
        ).lower()
        auth_secret = os.getenv(
            "MVP_AUTH_SECRET",
            "local-pilot-secret-change-me",
        )
        auth_ttl = int(
            os.getenv("MVP_AUTH_TTL_SECONDS", "86400")
        )
        auth_prefix = os.getenv(
            "MVP_AUTH_PREFIX",
            "aslan:mvp-auth",
        )

        secure_secret = (
            len(auth_secret) >= 32
            and "change-me" not in auth_secret.lower()
            and "secret" not in auth_secret.lower()
        )
        demo_disabled = (
            auth_secret
            != "local-pilot-secret-change-me"
        )
        ttl_valid = 900 <= auth_ttl <= 604800
        prefix_valid = (
            bool(auth_prefix.strip())
            and " " not in auth_prefix
        )

        blockers = []
        warnings = []
        if env == "production" and not secure_secret:
            blockers.append(
                "Production ortamında güçlü MVP_AUTH_SECRET gerekli"
            )
        if env == "production" and not demo_disabled:
            blockers.append(
                "Varsayılan demo secret production ortamında yasak"
            )
        if not ttl_valid:
            blockers.append(
                "Auth TTL 15 dakika ile 7 gün arasında olmalı"
            )
        if not prefix_valid:
            blockers.append(
                "Redis auth prefix geçersiz"
            )
        if env != "production":
            warnings.append(
                "Production güvenlik kontrolleri development modunda"
            )
        if auth_ttl > 86400:
            warnings.append(
                "Uzun oturum süresi hesap güvenliği riskini artırabilir"
            )
        if not warnings:
            warnings.append(
                "Belirgin güvenlik yapılandırma uyarısı yok"
            )

        return SecurityConfigurationReport(
            report_id=report_id,
            environment=env,
            secure_secret=secure_secret,
            default_demo_secret_disabled=demo_disabled,
            auth_ttl_valid=ttl_valid,
            redis_prefix_valid=prefix_valid,
            production_ready=not blockers,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )

    def create_backup(
        self,
        *,
        backup_id: str,
        club_id: str,
        now: int | None = None,
    ) -> BackupManifest:
        repo = self.workspace_service.repository
        club = repo.get_club(club_id)
        if club is None:
            raise KeyError("Kulüp bulunamadı")

        predictions = (
            self.intelligence_service.repository
            .list_predictions(club_id)
        )
        models = (
            self.intelligence_service.repository
            .list_models(club_id)
        )
        payload = {
            "schema_version": "build-016",
            "club": club.__dict__,
            "players": [
                item.__dict__
                for item in repo.list_players(club_id)
            ],
            "matches": [
                item.__dict__
                for item in repo.list_matches(club_id)
            ],
            "opponents": [
                item.__dict__
                for item in repo.list_opponents(club_id)
            ],
            "predictions": [
                {
                    **item.__dict__,
                    "likely_scores": list(item.likely_scores),
                    "factors": list(item.factors),
                    "risks": list(item.risks),
                }
                for item in predictions
            ],
            "models": [
                {
                    **item.__dict__,
                    "feature_set": list(item.feature_set),
                }
                for item in models
            ],
        }
        payload_json = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        checksum = hashlib.sha256(
            payload_json.encode("utf-8")
        ).hexdigest()
        counts = {
            key: len(payload[key])
            for key in (
                "players",
                "matches",
                "opponents",
                "predictions",
                "models",
            )
        }
        return BackupManifest(
            backup_id=backup_id,
            club_id=club_id,
            schema_version="build-016",
            entity_counts=counts,
            checksum=checksum,
            payload_json=payload_json,
            created_at=int(
                now if now is not None else time.time()
            ),
        )

    def validate_restore(
        self,
        *,
        validation_id: str,
        backup_id: str,
        payload_json: str,
        expected_checksum: str,
        now: int | None = None,
    ) -> RestoreValidationReport:
        errors = []
        checksum = hashlib.sha256(
            payload_json.encode("utf-8")
        ).hexdigest()
        checksum_valid = checksum == expected_checksum

        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            payload = {}
            errors.append("Backup JSON geçersiz")

        schema_valid = (
            payload.get("schema_version")
            == "build-016"
        )
        required_valid = all(
            section in payload
            for section in self.REQUIRED_SECTIONS
        )

        if not checksum_valid:
            errors.append("Backup checksum eşleşmiyor")
        if not schema_valid:
            errors.append("Backup schema version uyumsuz")
        if not required_valid:
            errors.append("Backup zorunlu bölümleri eksik")

        return RestoreValidationReport(
            validation_id=validation_id,
            backup_id=backup_id,
            checksum_valid=checksum_valid,
            schema_valid=schema_valid,
            required_sections_valid=required_valid,
            restorable=(
                checksum_valid
                and schema_valid
                and required_valid
            ),
            errors=tuple(errors),
            validated_at=int(
                now if now is not None else time.time()
            ),
        )

    def contract_snapshot(
        self,
        *,
        snapshot_id: str,
        api_version: str,
        routes: tuple[str, ...],
        now: int | None = None,
    ) -> ContractSnapshot:
        normalized = tuple(sorted(set(routes)))
        checksum = hashlib.sha256(
            json.dumps(
                normalized,
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        return ContractSnapshot(
            snapshot_id=snapshot_id,
            api_version=api_version,
            routes=normalized,
            checksum=checksum,
            created_at=int(
                now if now is not None else time.time()
            ),
        )
