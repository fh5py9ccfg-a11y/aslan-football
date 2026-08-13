from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class RecoverableSecretProvider(Protocol):
    def deactivate_version(self, name: str, version: str) -> None: ...
    def reactivate_previous(self, name: str) -> None: ...


@dataclass(frozen=True)
class RotationRecoveryResult:
    secret_name: str
    failed_version: str
    recovered: bool
    steps: tuple[str, ...]


class SecretRotationRecovery:
    def __init__(self, provider: RecoverableSecretProvider):
        self.provider = provider

    def recover(
        self,
        *,
        secret_name: str,
        failed_version: str,
        previous_retired: bool,
    ) -> RotationRecoveryResult:
        if not secret_name.strip() or not failed_version.strip():
            raise ValueError("Secret adı ve sürümü boş olamaz")

        steps = []
        self.provider.deactivate_version(secret_name, failed_version)
        steps.append("failed-version-deactivated")

        if previous_retired:
            self.provider.reactivate_previous(secret_name)
            steps.append("previous-version-reactivated")

        return RotationRecoveryResult(
            secret_name=secret_name,
            failed_version=failed_version,
            recovered=True,
            steps=tuple(steps),
        )
