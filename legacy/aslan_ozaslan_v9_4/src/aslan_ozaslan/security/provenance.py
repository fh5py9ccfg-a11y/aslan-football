from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac


@dataclass(frozen=True)
class ImageProvenance:
    image_reference: str
    builder: str
    source_revision: str
    signature: str


class ProvenanceVerifier:
    def __init__(self, verification_key: bytes):
        if len(verification_key) < 32:
            raise ValueError("Doğrulama anahtarı en az 32 bayt olmalıdır")
        self.verification_key = verification_key

    def sign(self, image_reference: str, builder: str, source_revision: str) -> ImageProvenance:
        payload = self._payload(image_reference, builder, source_revision)
        signature = hmac.new(
            self.verification_key,
            payload,
            hashlib.sha256,
        ).hexdigest()
        return ImageProvenance(
            image_reference=image_reference,
            builder=builder,
            source_revision=source_revision,
            signature=signature,
        )

    def verify(self, provenance: ImageProvenance) -> bool:
        expected = hmac.new(
            self.verification_key,
            self._payload(
                provenance.image_reference,
                provenance.builder,
                provenance.source_revision,
            ),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, provenance.signature)

    def _payload(self, image_reference: str, builder: str, source_revision: str) -> bytes:
        if not image_reference.strip() or not builder.strip() or not source_revision.strip():
            raise ValueError("Provenance alanları boş olamaz")
        return f"{image_reference}|{builder}|{source_revision}".encode("utf-8")
