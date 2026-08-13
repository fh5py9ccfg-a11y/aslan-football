from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class CosignVerificationResult:
    image_reference: str
    certificate_identity: str
    issuer: str
    verified: bool


class CosignVerifier:
    def __init__(
        self,
        verifier: Callable[[str, str, str], bool],
        *,
        expected_identity: str,
        expected_issuer: str,
    ):
        self.verifier = verifier
        self.expected_identity = expected_identity
        self.expected_issuer = expected_issuer

    def verify(self, image_reference: str) -> CosignVerificationResult:
        if "@sha256:" not in image_reference:
            raise ValueError("Cosign doğrulaması digest gerektirir")

        verified = bool(
            self.verifier(
                image_reference,
                self.expected_identity,
                self.expected_issuer,
            )
        )
        return CosignVerificationResult(
            image_reference=image_reference,
            certificate_identity=self.expected_identity,
            issuer=self.expected_issuer,
            verified=verified,
        )
