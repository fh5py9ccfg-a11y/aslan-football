from __future__ import annotations

import base64
import hashlib
import hmac
import os


class PasswordHasher:
    algorithm = "scrypt"

    def hash(self, password: str) -> str:
        self._validate(password)
        salt = os.urandom(16)
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            dklen=32,
        )
        return "$".join(
            [
                self.algorithm,
                base64.urlsafe_b64encode(salt).decode("ascii"),
                base64.urlsafe_b64encode(digest).decode("ascii"),
            ]
        )

    def verify(self, password: str, encoded: str) -> bool:
        try:
            algorithm, salt_text, digest_text = encoded.split("$", 2)
            if algorithm != self.algorithm:
                return False
            salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
            expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
            actual = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt,
                n=2**14,
                r=8,
                p=1,
                dklen=len(expected),
            )
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False

    def _validate(self, password: str) -> None:
        if len(password) < 12:
            raise ValueError("Parola en az 12 karakter olmalıdır")
        if password.lower() == password or password.upper() == password:
            raise ValueError("Parola büyük ve küçük harf içermelidir")
        if not any(char.isdigit() for char in password):
            raise ValueError("Parola rakam içermelidir")
