from __future__ import annotations
from dataclasses import dataclass
import base64
import time

import httpx

from .cache_resilience import CacheHealth, MetadataCircuitBreaker

@dataclass(frozen=True)
class JwkRecord:
    kid: str
    kty: str
    alg: str
    use: str | None
    n: str
    e: str

class JwksCache:
    def __init__(
        self,
        *,
        jwks_url: str,
        ttl_seconds: int = 300,
        stale_if_error_seconds: int = 3600,
        client: httpx.Client | None = None,
        circuit_breaker: MetadataCircuitBreaker | None = None,
    ):
        if not jwks_url.strip():
            raise ValueError("jwks_url boş olamaz")
        if ttl_seconds <= 0 or stale_if_error_seconds < 0:
            raise ValueError("Cache süreleri geçersiz")

        self.jwks_url = jwks_url
        self.ttl_seconds = ttl_seconds
        self.stale_if_error_seconds = stale_if_error_seconds
        self.client = client or httpx.Client(timeout=10.0)
        self._owns_client = client is None
        self.breaker = circuit_breaker or MetadataCircuitBreaker()
        self._items: dict[str, JwkRecord] = {}
        self._expires_at = 0.0
        self._stale_until = 0.0
        self._last_success_at: float | None = None
        self._last_error: str | None = None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def get(
        self,
        kid: str,
        *,
        now: float | None = None,
    ) -> JwkRecord:
        current = now if now is not None else time.time()

        if (
            kid in self._items
            and current < self._expires_at
        ):
            return self._items[kid]

        if not self.breaker.allow(now=current):
            if (
                kid in self._items
                and current < self._stale_until
            ):
                return self._items[kid]
            raise RuntimeError("JWKS circuit breaker açık")

        try:
            self.refresh(now=current)
        except Exception as exc:
            self._last_error = str(exc)
            self.breaker.failure(now=current)
            if (
                kid in self._items
                and current < self._stale_until
            ):
                return self._items[kid]
            raise

        try:
            return self._items[kid]
        except KeyError as exc:
            raise ValueError("JWKS kid bulunamadı") from exc

    def refresh(
        self,
        *,
        now: float | None = None,
    ) -> None:
        response = self.client.get(self.jwks_url)
        response.raise_for_status()
        payload = response.json()
        keys = payload.get("keys")
        if not isinstance(keys, list):
            raise ValueError("JWKS keys alanı geçersiz")

        items = {}
        for item in keys:
            if (
                item.get("kty") == "RSA"
                and item.get("kid")
                and item.get("n")
                and item.get("e")
            ):
                record = JwkRecord(
                    kid=str(item["kid"]),
                    kty=str(item["kty"]),
                    alg=str(item.get("alg") or "RS256"),
                    use=(
                        str(item["use"])
                        if item.get("use") is not None
                        else None
                    ),
                    n=str(item["n"]),
                    e=str(item["e"]),
                )
                items[record.kid] = record

        if not items:
            raise ValueError("JWKS içinde kullanılabilir RSA key yok")

        current = now if now is not None else time.time()
        self._items = items
        self._expires_at = current + self.ttl_seconds
        self._stale_until = (
            self._expires_at + self.stale_if_error_seconds
        )
        self._last_success_at = current
        self._last_error = None
        self.breaker.success()

    def health(
        self,
        *,
        now: float | None = None,
    ) -> CacheHealth:
        current = now if now is not None else time.time()
        if not self._items:
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

def b64url_to_int(value: str) -> int:
    padded = value + "=" * (-len(value) % 4)
    return int.from_bytes(
        base64.urlsafe_b64decode(
            padded.encode("ascii")
        ),
        "big",
    )
