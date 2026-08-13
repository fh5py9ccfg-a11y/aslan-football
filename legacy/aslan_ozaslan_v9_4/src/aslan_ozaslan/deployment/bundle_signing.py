from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json


@dataclass(frozen=True)
class SignedDeploymentBundle:
    manifest_digest: str
    signer: str
    signature: str


class DeploymentBundleSigner:
    def __init__(self, key: bytes, signer: str):
        if len(key) < 32:
            raise ValueError("İmzalama anahtarı en az 32 bayt olmalıdır")
        if not signer.strip():
            raise ValueError("Signer boş olamaz")
        self.key = key
        self.signer = signer

    def sign(self, documents: list[str]) -> SignedDeploymentBundle:
        digest = self._digest(documents)
        signature = hmac.new(
            self.key,
            f"{self.signer}|{digest}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return SignedDeploymentBundle(
            manifest_digest=digest,
            signer=self.signer,
            signature=signature,
        )

    def verify(self, documents: list[str], signed: SignedDeploymentBundle) -> bool:
        digest = self._digest(documents)
        if digest != signed.manifest_digest:
            return False
        expected = hmac.new(
            self.key,
            f"{signed.signer}|{digest}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signed.signature)

    def _digest(self, documents: list[str]) -> str:
        canonical = []
        for document in documents:
            payload = json.loads(document)
            canonical.append(
                json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            )
        raw = "\n---\n".join(sorted(canonical)).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
