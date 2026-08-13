from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class ManifestValidationReport:
    valid: bool
    errors: tuple[str, ...]


class DeploymentBundleValidator:
    REQUIRED_KINDS = {"Namespace", "Deployment", "Service", "Ingress", "NetworkPolicy"}

    def validate(self, documents: list[str]) -> ManifestValidationReport:
        errors = []
        kinds = set()

        for index, document in enumerate(documents):
            try:
                payload = json.loads(document)
            except json.JSONDecodeError:
                errors.append(f"invalid_json:{index}")
                continue

            kind = payload.get("kind")
            if not kind:
                errors.append(f"missing_kind:{index}")
                continue
            kinds.add(kind)

            metadata = payload.get("metadata") or {}
            if not metadata.get("name"):
                errors.append(f"missing_name:{index}")

            if kind == "Deployment":
                containers = (
                    payload.get("spec", {})
                    .get("template", {})
                    .get("spec", {})
                    .get("containers", [])
                )
                if not containers:
                    errors.append(f"deployment_without_container:{index}")
                for container in containers:
                    image = container.get("image", "")
                    if "@sha256:" not in image:
                        errors.append(f"deployment_image_not_immutable:{index}")

        missing = sorted(self.REQUIRED_KINDS - kinds)
        errors.extend(f"missing_kind:{kind}" for kind in missing)

        return ManifestValidationReport(
            valid=not errors,
            errors=tuple(errors),
        )
