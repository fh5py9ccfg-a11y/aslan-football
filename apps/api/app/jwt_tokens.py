from dataclasses import dataclass
import base64, hashlib, hmac, json, secrets, time

@dataclass(frozen=True)
class JwtPrincipal:
    subject: str
    roles: tuple[str, ...]
    token_id: str
    expires_at: int
    issuer: str
    audience: str
    key_id: str

class SigningKeyRing:
    def __init__(self):
        self._keys = {}
        self._active = None

    def add(self, *, key_id, secret, activate=False):
        if len(secret) < 16:
            raise ValueError("JWT secret en az 16 karakter olmalıdır")
        self._keys[key_id] = secret.encode()
        if activate or self._active is None:
            self._active = key_id

    def active(self):
        if self._active is None:
            raise RuntimeError("Aktif JWT key yok")
        return self._active, self._keys[self._active]

    def get(self, key_id):
        if key_id not in self._keys:
            raise ValueError("JWT kid bilinmiyor")
        return self._keys[key_id]

    def public_metadata(self):
        return tuple({
            "kid": key_id,
            "alg": "HS256",
            "use": "sig",
            "active": key_id == self._active,
        } for key_id in sorted(self._keys))

class JwtTokenService:
    def __init__(self, *, key_ring, issuer, audience, revocation_repository=None):
        self.key_ring = key_ring
        self.issuer = issuer
        self.audience = audience
        self.revocations = revocation_repository

    def issue_access_token(self, *, subject, roles, ttl_seconds=900):
        now = int(time.time())
        kid, secret = self.key_ring.active()
        header = {"alg": "HS256", "typ": "JWT", "kid": kid}
        payload = {
            "sub": subject,
            "roles": list(roles),
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "nbf": now,
            "exp": now + ttl_seconds,
            "jti": secrets.token_urlsafe(16),
            "token_use": "access",
        }
        head = self._b64_json(header)
        body = self._b64_json(payload)
        signing_input = f"{head}.{body}"
        sig = self._b64(hmac.new(
            secret, signing_input.encode(), hashlib.sha256
        ).digest())
        return f"{signing_input}.{sig}"

    def verify_access_token(self, token, *, now=None):
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("JWT biçimi geçersiz")
        head, body, signature = parts
        header = json.loads(self._decode(head))
        payload = json.loads(self._decode(body))
        secret = self.key_ring.get(str(header.get("kid") or ""))
        expected = self._b64(hmac.new(
            secret, f"{head}.{body}".encode(), hashlib.sha256
        ).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("JWT imzası geçersiz")
        current = int(now if now is not None else time.time())
        if payload.get("iss") != self.issuer:
            raise ValueError("JWT issuer geçersiz")
        if payload.get("aud") != self.audience:
            raise ValueError("JWT audience geçersiz")
        if int(payload.get("nbf", 0)) > current:
            raise ValueError("JWT henüz geçerli değil")
        expires_at = int(payload.get("exp", 0))
        if expires_at <= current:
            raise ValueError("JWT süresi dolmuş")
        if payload.get("token_use") != "access":
            raise ValueError("Token access token değil")
        jti = str(payload.get("jti") or "")
        sub = str(payload.get("sub") or "")
        if not jti or not sub:
            raise ValueError("JWT alanları eksik")
        if self.revocations and self.revocations.is_revoked(jti):
            raise ValueError("JWT iptal edilmiş")
        return JwtPrincipal(
            subject=sub,
            roles=tuple(str(x) for x in payload.get("roles") or ()),
            token_id=jti,
            expires_at=expires_at,
            issuer=self.issuer,
            audience=self.audience,
            key_id=str(header["kid"]),
        )

    def revoke(self, token):
        p = self.verify_access_token(token)
        if self.revocations is None:
            raise RuntimeError("Revocation repository yok")
        self.revocations.revoke(p.token_id, p.expires_at)

    @staticmethod
    def _b64(data):
        return base64.urlsafe_b64encode(data).decode().rstrip("=")

    @classmethod
    def _b64_json(cls, value):
        return cls._b64(json.dumps(
            value, separators=(",", ":"), sort_keys=True
        ).encode())

    @staticmethod
    def _decode(value):
        return base64.urlsafe_b64decode(
            (value + "=" * (-len(value) % 4)).encode()
        ).decode()
