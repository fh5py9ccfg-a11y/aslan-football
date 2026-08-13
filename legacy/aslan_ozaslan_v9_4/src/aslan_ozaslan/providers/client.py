from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from aslan_ozaslan.resilience import CircuitBreaker


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderResponse:
    provider_name: str
    resource_type: str
    external_id: str
    payload: dict[str, Any]


class ProviderClient(Protocol):
    name: str

    def fetch(self, resource_type: str, external_id: str) -> ProviderResponse:
        ...


class SafeProviderExecutor:
    def __init__(self, client: ProviderClient, breaker: CircuitBreaker):
        self.client = client
        self.breaker = breaker

    def fetch(self, resource_type: str, external_id: str) -> ProviderResponse:
        if not self.breaker.allow_request():
            raise ProviderError(f"Sağlayıcı devresi açık: {self.client.name}")

        try:
            response = self.client.fetch(resource_type, external_id)
        except Exception as exc:
            self.breaker.record_failure()
            raise ProviderError(
                f"Sağlayıcı çağrısı başarısız: {self.client.name}"
            ) from exc

        if response.provider_name != self.client.name:
            self.breaker.record_failure()
            raise ProviderError("Sağlayıcı kimliği uyuşmuyor")
        if response.external_id != external_id:
            self.breaker.record_failure()
            raise ProviderError("İstenen kayıt ile dönen kayıt uyuşmuyor")

        self.breaker.record_success()
        return response
