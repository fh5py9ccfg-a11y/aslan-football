from apps.api.app.supply_chain_security import (
    SupplyChainSecurityService,
)


def test_sbom_passes_known_licenses():
    service = SupplyChainSecurityService()
    report = service.sbom_report(
        report_id="s1",
        build_version="build-024",
        dependencies=(
            {
                "name": "fastapi",
                "version": "1.0.0",
                "source": "pypi",
                "license": "MIT",
            },
            {
                "name": "redis",
                "version": "5.0.0",
                "source": "pypi",
                "license": "BSD-3-Clause",
            },
        ),
        now=100,
    )

    assert report.status == "PASS"
    assert report.dependency_count == 2
    assert report.unknown_licenses == 0
    assert len(report.checksum) == 64


def test_sbom_blocks_forbidden_license():
    service = SupplyChainSecurityService()
    report = service.sbom_report(
        report_id="s1",
        build_version="build-024",
        dependencies=(
            {
                "name": "bad-lib",
                "version": "1.0",
                "source": "private",
                "license": "AGPL-3.0",
            },
        ),
        now=100,
    )

    assert report.status == "BLOCKED"
    assert report.forbidden_licenses == 1


def test_reproducible_build_check():
    service = SupplyChainSecurityService()
    first = {"files": ["a", "b"], "version": "1"}
    second = {"version": "1", "files": ["a", "b"]}

    report = service.reproducible_build_report(
        report_id="r1",
        first_manifest=first,
        second_manifest=second,
        now=100,
    )

    assert report.deterministic is True
    assert report.status == "PASS"


def test_package_integrity_check():
    service = SupplyChainSecurityService()
    package = b"package"
    import hashlib
    import json

    expected = hashlib.sha256(package).hexdigest()
    manifest = {"version": "1", "files": 10}
    manifest_checksum = hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    report = service.package_integrity_report(
        report_id="p1",
        package_bytes=package,
        expected_checksum=expected,
        manifest=manifest,
        expected_manifest_checksum=manifest_checksum,
        now=100,
    )

    assert report.status == "PASS"
    assert report.checksum_valid is True
    assert report.manifest_valid is True
