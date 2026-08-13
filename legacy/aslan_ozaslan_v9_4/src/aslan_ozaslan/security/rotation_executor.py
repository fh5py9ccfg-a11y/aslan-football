from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .secret_rotation import SecretRotationDecision


class RotatableSecretProvider(Protocol):
    def create_version(self, name: str) -> str: ...
    def activate_version(self, name: str, version: str) -> None: ...
    def retire_previous(self, name: str) -> None: ...


@dataclass(frozen=True)
class SecretRotationExecution:
    secret_name: str
    new_version: str
    activated: bool
    previous_retired: bool


class SecretRotationExecutor:
    def __init__(self, provider: RotatableSecretProvider):
        self.provider = provider

    def execute(
        self,
        secret_name: str,
        decision: SecretRotationDecision,
        *,
        retire_previous: bool,
    ) -> SecretRotationExecution:
        if not decision.due:
            raise ValueError("Secret rotasyonu henüz zamanı gelmedi")
        if not secret_name.strip():
            raise ValueError("Secret adı boş olamaz")

        version = self.provider.create_version(secret_name)
        if not version.strip():
            raise RuntimeError("Yeni secret sürümü oluşturulamadı")

        self.provider.activate_version(secret_name, version)

        retired = False
        if retire_previous:
            self.provider.retire_previous(secret_name)
            retired = True

        return SecretRotationExecution(
            secret_name=secret_name,
            new_version=version,
            activated=True,
            previous_retired=retired,
        )
