import pytest

from apps.api.app.release_manifest import (
    ReleaseComponent,
    ReleaseIntegrityError,
    ReleaseManifestBuilder,
)


def test_release_manifest_is_verifiable():
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

    assert builder.verify(manifest) is True
    assert len(manifest.manifest_sha256) == 64


def test_tampered_manifest_is_rejected():
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
    tampered = manifest.__class__(
        **{
            **manifest.__dict__,
            "version": "11.0.1",
        }
    )

    with pytest.raises(ReleaseIntegrityError):
        builder.verify(tampered)
