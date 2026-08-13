from __future__ import annotations
from dataclasses import dataclass
import time
import httpx

from .cache_resilience import CacheHealth, MetadataCircuitBreaker

@dataclass(frozen=True)
class OidcProviderMetadata:
    issuer: str
    jwks_uri: str
    authorization_endpoint: str | None
    token_endpoint: str | None
    end_session_endpoint: str | None
    scopes_supported: tuple[str, ...]
    response_types_supported: tuple[str, ...]

class OidcDiscoveryCache:
    def __init__(
        self,
        *,
        issuer: str,
        ttl_seconds: int = 3600,
        stale_if_error_seconds: int = 21600,
        client: httpx.Client | None = None,
        circuit_breaker: MetadataCircuitBreaker | None = None,
    ):
        if not issuer.strip():
            raise ValueError("issuer boş olamaz")
        if ttl_seconds <= 0 or stale_if_error_seconds < 0:
            raise ValueError("Cache süreleri geçersiz")

        self.issuer = issuer.rstrip("/")
        self.discovery_url = (
            f"{self.issuer}/.well-known/openid-configuration"
        )
        self.ttl_seconds = ttl_seconds
        self.stale_if_error_seconds = stale_if_error_seconds
        self.client = client or httpx.Client(timeout=10.0)
        self._owns_client = client is None
        self.breaker = circuit_breaker or MetadataCircuitBreaker()
        self._metadata: OidcProviderMetadata | None = None
        self._expires_at = 0.0
        self._stale_until = 0.0
        self._last_success_at: float | None = None
        self._last_error: str | None = None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def get(
        self,
        *,
        now: float | None = None,
        force_refresh: bool = False,
    ) -> OidcProviderMetadata:
        current = now if now is not None else time.time()
        if (
            not force_refresh
            and self._metadata is not None
            and current < self._expires_at
        ):
            return self._metadata

        if not self.breaker.allow(now=current):
            if (
                self._metadata is not None
                and current < self._stale_until
            ):
                return self._metadata
            raise RuntimeError("OIDC discovery circuit breaker açık")

        try:
            return self.refresh(now=current)
        except Exception as exc:
            self._last_error = str(exc)
            self.breaker.failure(now=current)
            if (
                self._metadata is not None
                and current < self._stale_until
            ):
                return self._metadata
            raise

    def refresh(
        self,
        *,
        now: float | None = None,
    ) -> OidcProviderMetadata:
        response = self.client.get(self.discovery_url)
        response.raise_for_status()
        payload = response.json()

        issuer = str(payload.get("issuer") or "").rstrip("/")
        jwks_uri = str(payload.get("jwks_uri") or "")
        if issuer != self.issuer:
            raise ValueError("Discovery issuer uyuşmuyor")
        if not jwks_uri:
            raise ValueError("Discovery jwks_uri eksik")

        metadata = OidcProviderMetadata(
            issuer=issuer,
            jwks_uri=jwks_uri,
            authorization_endpoint=(
                str(payload["authorization_endpoint"])
                if payload.get("authorization_endpoint")
                else None
            ),
            token_endpoint=(
                str(payload["token_endpoint"])
                if payload.get("token_endpoint")
                else None
            ),
            end_session_endpoint=(
                str(payload["end_session_endpoint"])
                if payload.get("end_session_endpoint")
                else None
            ),
            scopes_supported=tuple(
                str(item)
                for item in payload.get("scopes_supported") or ()
            ),
            response_types_supported=tuple(
                str(item)
                for item in payload.get(
                    "response_types_supported"
                ) or ()
            ),
        )
        current = now if now is not None else time.time()
        self._metadata = metadata
        self._expires_at = current + self.ttl_seconds
        self._stale_until = (
            self._expires_at + self.stale_if_error_seconds
        )
        self._last_success_at = current
        self._last_error = None
        self.breaker.success()
        return metadata

    def health(
        self,
        *,
        now: float | None = None,
    ) -> CacheHealth:
        current = now if now is not None else time.time()
        if self._metadata is None:
            status = "empty"
        elif current < self._expires_at:
            status = "fresh"
        elif current < self._stale_until:
            status = "stale"
        else:
            status = "expired"

        return CacheHealth(
            status=status,
            last_success_at=self._last_success_at,
            last_error=self._last_error,
            expires_at=self._expires_at,
            stale_until=self._stale_until,
        )
