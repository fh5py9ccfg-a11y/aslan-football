from __future__ import annotations

from dataclasses import dataclass

from .bundle_signing import DeploymentBundleSigner, SignedDeploymentBundle
from .bundle_validator import DeploymentBundleValidator


@dataclass(frozen=True)
class SignedPipelineReport:
    allowed: bool
    validation_errors: tuple[str, ...]
    signature_valid: bool


class SignedDeploymentPipelineGate:
    def __init__(
        self,
        validator: DeploymentBundleValidator,
        signer: DeploymentBundleSigner,
    ):
        self.validator = validator
        self.signer = signer

    def evaluate(
        self,
        documents: list[str],
        signed_bundle: SignedDeploymentBundle,
    ) -> SignedPipelineReport:
        validation = self.validator.validate(documents)
        signature_valid = self.signer.verify(documents, signed_bundle)

        return SignedPipelineReport(
            allowed=validation.valid and signature_valid,
            validation_errors=validation.errors,
            signature_valid=signature_valid,
        )
