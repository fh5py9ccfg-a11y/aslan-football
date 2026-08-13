from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ProductionEnvironmentInput:
    https_enabled: bool
    secure_secrets: bool
    database_backup_ready: bool
    monitoring_ready: bool
    alerting_ready: bool
    provider_token_available: bool
    rollback_ready: bool

@dataclass(frozen=True)
class ProductionEnvironmentReport:
    ready: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

class ProductionEnvironmentAuditor:
    def audit(self, item: ProductionEnvironmentInput) -> ProductionEnvironmentReport:
        blockers = []
        warnings = []

        if not item.https_enabled:
            blockers.append("https_not_enabled")
        if not item.secure_secrets:
            blockers.append("secure_secret_storage_missing")
        if not item.database_backup_ready:
            blockers.append("database_backup_not_ready")
        if not item.monitoring_ready:
            blockers.append("monitoring_not_ready")
        if not item.provider_token_available:
            blockers.append("provider_token_missing")
        if not item.rollback_ready:
            blockers.append("rollback_not_ready")
        if not item.alerting_ready:
            warnings.append("alerting_not_ready")

        return ProductionEnvironmentReport(
            ready=not blockers,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
        )
