from __future__ import annotations
import hashlib
import hmac
import secrets

class CsrfManager:
    def __init__(self, secret: bytes | None = None):
        self.secret = secret or secrets.token_bytes(32)

    def issue(self, session_token: str) -> str:
        nonce = secrets.token_urlsafe(18)
        payload = f"{session_token}:{nonce}".encode("utf-8")
        signature = hmac.new(self.secret, payload, hashlib.sha256).hexdigest()
        return f"{nonce}.{signature}"

    def validate(self, session_token: str, csrf_token: str) -> bool:
        try:
            nonce, provided = csrf_token.split(".", 1)
        except ValueError:
            return False
        payload = f"{session_token}:{nonce}".encode("utf-8")
        expected = hmac.new(self.secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(provided, expected)
