from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class AppSettings:
    environment: str
    database_dsn: str
    redis_url: str
    session_secret: str
    backup_key: str
    public_base_url: str
    admin_enabled: bool = True


class SettingsValidator:
    VALID_ENVIRONMENTS = {"development", "test", "staging", "production"}

    def validate(self, settings: AppSettings) -> tuple[str, ...]:
        errors: list[str] = []

        if settings.environment not in self.VALID_ENVIRONMENTS:
            errors.append("environment_invalid")

        if settings.environment == "production":
            if not settings.database_dsn.startswith(("postgresql://", "postgres://")):
                errors.append("production_database_must_be_postgresql")
            if not settings.redis_url.startswith(("redis://", "rediss://")):
                errors.append("production_redis_required")
            if len(settings.session_secret) < 32:
                errors.append("session_secret_too_short")
            if len(settings.backup_key) < 32:
                errors.append("backup_key_too_short")
            parsed = urlparse(settings.public_base_url)
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append("production_https_required")

        if settings.admin_enabled and not settings.session_secret:
            errors.append("admin_requires_session_secret")

        return tuple(errors)

    def require_valid(self, settings: AppSettings) -> None:
        errors = self.validate(settings)
        if errors:
            raise ValueError(",".join(errors))
