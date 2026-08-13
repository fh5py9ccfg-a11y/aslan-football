from __future__ import annotations
import hashlib
import json

class PayloadFingerprint:
    def calculate(self, payload: dict) -> str:
        if not isinstance(payload, dict):
            raise ValueError("payload sözlük olmalıdır")
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
