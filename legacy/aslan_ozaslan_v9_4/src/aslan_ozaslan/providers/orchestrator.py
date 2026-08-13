from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from aslan_ozaslan.providers.retry import RetryPolicy
from aslan_ozaslan.resilience import CircuitBreaker


class ProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderAttempt:
    provider_name: str
    succeeded: bool
    reason: str


@dataclass
class _ProviderEntry:
    name: str
    priority: int
    fetcher: Callable[[str], Any]
    breaker: CircuitBreaker
    retry_policy: RetryPolicy


class ProviderOrchestrator:
    def __init__(self, sleeper: Callable[[float], None] | None = None):
        self._providers: list[_ProviderEntry] = []
        self._sleeper = sleeper or (lambda seconds: None)

    def register(
        self,
        *,
        name: str,
        priority: int,
        fetcher: Callable[[str], Any],
        breaker: CircuitBreaker | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        if any(item.name == name for item in self._providers):
            raise ValueError(f"Sağlayıcı zaten kayıtlı: {name}")
        self._providers.append(
            _ProviderEntry(
                name=name,
                priority=priority,
                fetcher=fetcher,
                breaker=breaker or CircuitBreaker(),
                retry_policy=retry_policy or RetryPolicy(),
            )
        )
        self._providers.sort(key=lambda item: (item.priority, item.name))

    def fetch(self, resource_id: str) -> tuple[Any, tuple[ProviderAttempt, ...]]:
        if not resource_id.strip():
            raise ValueError("resource_id zorunludur")

        attempts: list[ProviderAttempt] = []
        for provider in self._providers:
            if not provider.breaker.allow_request():
                attempts.append(ProviderAttempt(provider.name, False, "Circuit breaker açık."))
                continue

            try:
                value = provider.retry_policy.run(
                    lambda: provider.fetcher(resource_id),
                    sleeper=self._sleeper,
                )
                if value is None:
                    raise LookupError("Sağlayıcı boş veri döndürdü.")
                provider.breaker.record_success()
                attempts.append(ProviderAttempt(provider.name, True, "Veri alındı."))
                return value, tuple(attempts)
            except (TimeoutError, ConnectionError, LookupError) as exc:
                provider.breaker.record_failure()
                attempts.append(ProviderAttempt(provider.name, False, str(exc)))

        raise ProviderUnavailable(
            "Hiçbir sağlayıcı güvenilir veri döndüremedi. "
            + "; ".join(f"{a.provider_name}: {a.reason}" for a in attempts)
        )
