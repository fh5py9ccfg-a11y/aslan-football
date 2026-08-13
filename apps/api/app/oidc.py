from __future__ import annotations
from dataclasses import dataclass
import base64
import json
import time

from .claim_mapping import ClaimMapper, ClaimMapping
from .jwks import JwksCache, b64url_to_int

@dataclass(frozen=True)
class OidcPrincipal:
    subject: str
    roles: tuple[str, ...]
    token_id: str
    issuer: str
    audience: str
    expires_at: int
    key_id: str

class OidcTokenVerifier:
    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_cache: JwksCache,
        clock_skew_seconds: int = 30,
        claim_mapper: ClaimMapper | None = None,
        allowed_issuers: tuple[str, ...] | None = None,
    ):
        if not issuer.strip() or not audience.strip():
            raise ValueError("issuer ve audience boş olamaz")
        if clock_skew_seconds < 0:
            raise ValueError("clock_skew_seconds negatif olamaz")

        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.jwks_cache = jwks_cache
        self.clock_skew_seconds = clock_skew_seconds
        self.claim_mapper = claim_mapper or ClaimMapper(
            ClaimMapping.from_json(None)
        )
        self.allowed_issuers = tuple(
            item.rstrip("/")
            for item in (
                allowed_issuers
                or (self.issuer,)
            )
        )

    def verify(
        self,
        token: str,
        *,
        now: int | None = None,
    ) -> OidcPrincipal:
        header, payload, signing_input, signature = (
            self._decode_token(token)
        )
        if header.get("alg") != "RS256":
            raise ValueError("OIDC token alg desteklenmiyor")

        kid = str(header.get("kid") or "")
        if not kid:
            raise ValueError("OIDC token kid eksik")
        jwk = self.jwks_cache.get(kid)

        self._verify_rs256(
            signing_input=signing_input,
            signature=signature,
            modulus=b64url_to_int(jwk.n),
            exponent=b64url_to_int(jwk.e),
        )

        current = int(now if now is not None else time.time())
        skew = self.clock_skew_seconds

        issuer = str(payload.get("iss") or "").rstrip("/")
        if issuer not in self.allowed_issuers:
            raise ValueError("OIDC issuer izinli değil")

        aud = payload.get("aud")
        audiences = (
            tuple(str(item) for item in aud)
            if isinstance(aud, list)
            else (str(aud),)
        )
        if self.audience not in audiences:
            raise ValueError("OIDC audience geçersiz")

        expires_at = int(payload.get("exp", 0))
        if expires_at + skew <= current:
            raise ValueError("OIDC token süresi dolmuş")
        if int(payload.get("nbf", 0)) - skew > current:
            raise ValueError("OIDC token henüz geçerli değil")

        subject = self.claim_mapper.subject(payload)
        token_id = str(payload.get("jti") or "")
        if not subject:
            raise ValueError("OIDC subject eksik")

        return OidcPrincipal(
            subject=subject,
            roles=self.claim_mapper.roles(payload),
            token_id=token_id,
            issuer=issuer,
            audience=self.audience,
            expires_at=expires_at,
            key_id=kid,
        )

    def _decode_token(
        self,
        token: str,
    ) -> tuple[dict, dict, bytes, bytes]:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("OIDC token biçimi geçersiz")

        head, body, sig = parts
        header = json.loads(self._decode(head))
        payload = json.loads(self._decode(body))
        signature = base64.urlsafe_b64decode(
            (sig + "=" * (-len(sig) % 4)).encode("ascii")
        )
        return (
            header,
            payload,
            f"{head}.{body}".encode("ascii"),
            signature,
        )

    @staticmethod
    def _decode(value: str) -> str:
        return base64.urlsafe_b64decode(
            (value + "=" * (-len(value) % 4)).encode("ascii")
        ).decode("utf-8")

    @staticmethod
    def _verify_rs256(
        *,
        signing_input: bytes,
        signature: bytes,
        modulus: int,
        exponent: int,
    ) -> None:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding, rsa
        from cryptography.exceptions import InvalidSignature

        public_key = rsa.RSAPublicNumbers(
            exponent,
            modulus,
        ).public_key()

        try:
            public_key.verify(
                signature,
                signing_input,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except InvalidSignature as exc:
            raise ValueError(
                "OIDC token imzası geçersiz"
            ) from exc
