from apps.api.app.sbom import (
    SbomBuilder,
    SoftwareComponent,
)


def test_sbom_contains_document_digest():
    sbom = SbomBuilder().build(
        document_name="aslan-platform",
        version="11.0.0-rc.1",
        components=(
            SoftwareComponent(
                name="fastapi",
                version="runtime",
                license="MIT",
                source="python-package",
                sha256="a" * 64,
            ),
        ),
    )

    assert sbom["bomFormat"] == "CycloneDX"
    assert len(sbom["documentSha256"]) == 64
    assert sbom["components"][0]["name"] == "fastapi"
