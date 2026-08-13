from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeploymentEnvironment:
    name: str
    replicas: int
    database_role: str
    redis_namespace: str
    public: bool


class EnvironmentRegistry:
    VALID_NAMES = {"development", "test", "staging", "production"}

    def __init__(self):
        self._items: dict[str, DeploymentEnvironment] = {}

    def register(self, environment: DeploymentEnvironment) -> None:
        if environment.name not in self.VALID_NAMES:
            raise ValueError("Geçersiz ortam")
        if environment.replicas <= 0:
            raise ValueError("Replica sayısı pozitif olmalıdır")
        if environment.name == "production" and environment.replicas < 2:
            raise ValueError("Production en az iki replica gerektirir")
        self._items[environment.name] = environment

    def get(self, name: str) -> DeploymentEnvironment:
        try:
            return self._items[name]
        except KeyError as exc:
            raise KeyError(f"Ortam kayıtlı değil: {name}") from exc
