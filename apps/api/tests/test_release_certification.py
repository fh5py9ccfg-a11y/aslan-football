from apps.api.app.release_manifest import (
    ReleaseCertification,
    ReleaseComponent,
    ReleaseManifestBuilder,
)


class Operations:
    def generate(self):
        return {
            "certified": True,
            "checks": [],
        }


def test_release_certification_requires_integrity():
    builder = ReleaseManifestBuilder()
    manifest = builder.build(
        release_id="r1",
        version="11.0.0-rc.1",
        channel="rc",
        build_id="build-1",
        source_revision="abc123",
        schema_version="11.0",
        minimum_rollback_version="10.48.0",
        components=(
            ReleaseComponent(
                name="api",
                version="11.0.0-rc.1",
                artifact_sha256="a" * 64,
                critical=True,
            ),
        ),
        now=100,
    )

    result = ReleaseCertification(
        manifest_builder=builder,
        operational_certification=Operations(),
    ).certify(manifest)

    assert result["certified"] is True
    assert result["component_integrity"] is True
