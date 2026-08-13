from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time


@dataclass(frozen=True)
class ReleaseComponent:
    name: str
    version: str
    artifact_sha256: str
    critical: bool


@dataclass(frozen=True)
class ReleaseManifest:
    release_id: str
    version: str
    channel: str
    build_id: str
    source_revision: str
    created_at: int
    schema_version: str
    minimum_rollback_version: str
    components: tuple[ReleaseComponent, ...]
    manifest_sha256: str


class ReleaseIntegrityError(RuntimeError):
    pass


class ReleaseManifestBuilder:
    def build(
        self,
        *,
        release_id: str,
        version: str,
        channel: str,
        build_id: str,
        source_revision: str,
        schema_version: str,
        minimum_rollback_version: str,
        components: tuple[ReleaseComponent, ...],
        now: int | None = None,
    ) -> ReleaseManifest:
        current = int(now if now is not None else time.time())
        payload = {
            "release_id": release_id,
            "version": version,
            "channel": channel,
            "build_id": build_id,
            "source_revision": source_revision,
            "created_at": current,
            "schema_version": schema_version,
            "minimum_rollback_version": minimum_rollback_version,
            "components": [
                item.__dict__
                for item in components
            ],
        }
        digest = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        return ReleaseManifest(
            release_id=release_id,
            version=version,
            channel=channel,
            build_id=build_id,
            source_revision=source_revision,
            created_at=current,
            schema_version=schema_version,
            minimum_rollback_version=(
                minimum_rollback_version
            ),
            components=components,
            manifest_sha256=digest,
        )

    def verify(self, manifest: ReleaseManifest) -> bool:
        payload = {
            "release_id": manifest.release_id,
            "version": manifest.version,
            "channel": manifest.channel,
            "build_id": manifest.build_id,
            "source_revision": manifest.source_revision,
            "created_at": manifest.created_at,
            "schema_version": manifest.schema_version,
            "minimum_rollback_version": (
                manifest.minimum_rollback_version
            ),
            "components": [
                item.__dict__
                for item in manifest.components
            ],
        }
        expected = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        if expected != manifest.manifest_sha256:
            raise ReleaseIntegrityError(
                "Release manifest bütünlüğü doğrulanamadı"
            )

        for component in manifest.components:
            if len(component.artifact_sha256) != 64:
                raise ReleaseIntegrityError(
                    f"Geçersiz component digest: {component.name}"
                )

        return True


class ReleaseCertification:
    def __init__(
        self,
        *,
        manifest_builder,
        operational_certification,
    ):
        self.manifest_builder = manifest_builder
        self.operational_certification = operational_certification

    def certify(
        self,
        manifest: ReleaseManifest,
    ) -> dict:
        self.manifest_builder.verify(manifest)
        operations = self.operational_certification.generate()

        critical_components = [
            item
            for item in manifest.components
            if item.critical
        ]
        component_integrity = all(
            len(item.artifact_sha256) == 64
            for item in critical_components
        )
        certified = (
            operations["certified"]
            and component_integrity
            and manifest.channel in {"stable", "rc"}
        )

        return {
            "certified": certified,
            "release_id": manifest.release_id,
            "version": manifest.version,
            "channel": manifest.channel,
            "manifest_sha256": manifest.manifest_sha256,
            "component_integrity": component_integrity,
            "operations": operations,
        }
