from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClusterService:
    name: str
    replicas: int
    image: str
    port: int
    readiness_path: str
    liveness_path: str


@dataclass(frozen=True)
class ClusterManifest:
    namespace: str
    services: tuple[ClusterService, ...]


class ClusterManifestValidator:
    def validate(self, manifest: ClusterManifest, *, production: bool) -> tuple[str, ...]:
        errors = []
        if not manifest.namespace.strip():
            errors.append("namespace_required")
        if not manifest.services:
            errors.append("services_required")

        seen = set()
        for service in manifest.services:
            if service.name in seen:
                errors.append(f"duplicate_service:{service.name}")
            seen.add(service.name)

            if service.replicas <= 0:
                errors.append(f"replicas_invalid:{service.name}")
            if production and service.replicas < 2:
                errors.append(f"production_replicas_too_low:{service.name}")
            if "@sha256:" not in service.image:
                errors.append(f"image_digest_required:{service.name}")
            if not 1 <= service.port <= 65535:
                errors.append(f"port_invalid:{service.name}")
            if not service.readiness_path.startswith("/"):
                errors.append(f"readiness_path_invalid:{service.name}")
            if not service.liveness_path.startswith("/"):
                errors.append(f"liveness_path_invalid:{service.name}")

        return tuple(errors)
