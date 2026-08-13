from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class CertificateStatus:
    common_name: str
    expires_at: datetime


@dataclass(frozen=True)
class CertificateAlert:
    expiring: bool
    days_remaining: int
    severity: str
    message: str


class CertificateExpiryMonitor:
    def __init__(self, warning_days: int = 30, critical_days: int = 7):
        if warning_days <= critical_days:
            raise ValueError("warning_days critical_days değerinden büyük olmalıdır")
        if critical_days < 0:
            raise ValueError("critical_days negatif olamaz")
        self.warning_days = warning_days
        self.critical_days = critical_days

    def evaluate(
        self,
        certificate: CertificateStatus,
        *,
        now: datetime | None = None,
    ) -> CertificateAlert:
        if certificate.expires_at.tzinfo is None:
            raise ValueError("expires_at timezone içermelidir")

        moment = now or datetime.now(timezone.utc)
        remaining_seconds = (certificate.expires_at - moment).total_seconds()
        days_remaining = int(remaining_seconds // 86400)

        if days_remaining <= self.critical_days:
            severity = "CRITICAL"
            expiring = True
        elif days_remaining <= self.warning_days:
            severity = "WARNING"
            expiring = True
        else:
            severity = "INFO"
            expiring = False

        return CertificateAlert(
            expiring=expiring,
            days_remaining=days_remaining,
            severity=severity,
            message=(
                f"{certificate.common_name} sertifikasının bitmesine "
                f"{days_remaining} gün kaldı"
            ),
        )
