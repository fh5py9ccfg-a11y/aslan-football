from __future__ import annotations
from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import os
import time
import secrets

from fastapi import Depends, Header, HTTPException, status

@dataclass(frozen=True)
class Principal:
    subject: str
    roles: tuple[str, ...]
    token_id: str = ""
    expires_at: int = 0

class TokenService:
    def __init__(
        self,
        secret: str,
        issuer: str = "aslan-ozaslan",
        revocation_repository=None,
    ):
        if len(secret) < 16:
            raise ValueError("Token secret en az 16 karakter olmalıdır")
        self.secret = secret.encode("utf-8")
        self.issuer = issuer
        self.revocations = revocation_repository

    def issue(
        self,
        *,
        subject: str,
        roles: tuple[str, ...],
        ttl_seconds: int = 3600,
    ) -> str:
        if not subject.strip():
            raise ValueError("subject boş olamaz")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds pozitif olmalıdır")
        now = int(time.time())
        payload = {
            "sub": subject,
            "roles": list(roles),
            "iss": self.issuer,
            "iat": now,
            "exp": now + ttl_seconds,
            "jti": secrets.token_urlsafe(16),
        }
        encoded = self._b64(
            json.dumps(
                payload,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        )
        signature = self._sign(encoded)
        return f"{encoded}.{signature}"

    def verify(self, token: str) -> Principal:
        try:
            encoded, signature = token.split(".", 1)
        except ValueError as exc:
            raise ValueError("Token biçimi geçersiz") from exc

        expected = self._sign(encoded)
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Token imzası geçersiz")

        payload = json.loads(
            base64.urlsafe_b64decode(self._pad(encoded)).decode("utf-8")
        )
        now = int(time.time())
        if payload.get("iss") != self.issuer:
            raise ValueError("Token issuer geçersiz")
        if int(payload.get("exp", 0)) <= now:
            raise ValueError("Token süresi dolmuş")

        subject = str(payload.get("sub") or "")
        roles = tuple(str(item) for item in payload.get("roles") or ())
        token_id = str(payload.get("jti") or "")
        expires_at = int(payload.get("exp", 0))
        if not subject or not token_id:
            raise ValueError("Token alanları eksik")
        if self.revocations is not None and self.revocations.is_revoked(token_id):
            raise ValueError("Token iptal edilmiş")
        return Principal(
            subject=subject,
            roles=roles,
            token_id=token_id,
            expires_at=expires_at,
        )

    def revoke(self, token: str) -> None:
        principal = self.verify(token)
        if self.revocations is None:
            raise RuntimeError("Revocation repository yapılandırılmamış")
        self.revocations.revoke(principal.token_id, principal.expires_at)

    def _sign(self, encoded: str) -> str:
        digest = hmac.new(
            self.secret,
            encoded.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return self._b64(digest)

    @staticmethod
    def _b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

    @staticmethod
    def _pad(value: str) -> bytes:
        return (value + "=" * (-len(value) % 4)).encode("ascii")

token_service = TokenService(
    os.getenv("AUTH_TOKEN_SECRET", "development-secret-change-me")
)

def current_principal(
    authorization: str | None = Header(default=None),
) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token gerekli",
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return token_service.verify(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

def require_roles(*required_roles: str):
    def dependency(
        principal: Principal = Depends(current_principal),
    ) -> Principal:
        if not set(required_roles).intersection(principal.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Yetersiz rol",
            )
        return principal
    return dependency
