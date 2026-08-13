from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time


@dataclass(frozen=True)
class DependencyRecord:
    name: str
    version: str
    source: str
    license: str
    checksum: str


@dataclass(frozen=True)
class SbomReport:
    report_id: str
    build_version: str
    dependencies: tuple[dict, ...]
    dependency_count: int
    unknown_licenses: int
    forbidden_licenses: int
    status: str
    checksum: str
    generated_at: int


@dataclass(frozen=True)
class ReproducibleBuildReport:
    report_id: str
    first_manifest_checksum: str
    second_manifest_checksum: str
    deterministic: bool
    status: str
    generated_at: int


@dataclass(frozen=True)
class PackageIntegrityReport:
    report_id: str
    expected_checksum: str
    actual_checksum: str
    checksum_valid: bool
    manifest_checksum: str
    manifest_valid: bool
    status: str
    generated_at: int


class SupplyChainValidationError(ValueError):
    pass


class SupplyChainSecurityService:
    FORBIDDEN_LICENSES = {
        "AGPL-3.0",
        "SSPL-1.0",
        "UNKNOWN-FORBIDDEN",
    }

    def sbom_report(
        self,
        *,
        report_id: str,
        build_version: str,
        dependencies: tuple[dict, ...],
        now: int | None = None,
    ) -> SbomReport:
        normalized = []
        unknown = 0
        forbidden = 0
        for item in dependencies:
            name = str(item.get("name", "")).strip()
            version = str(item.get("version", "")).strip()
            source = str(item.get("source", "pypi")).strip()
            license_name = str(
                item.get("license", "UNKNOWN")
            ).strip().upper()
            if not name or not version:
                raise SupplyChainValidationError(
                    "Bağımlılık adı ve sürümü zorunlu"
                )
            checksum = str(
                item.get("checksum", "")
            ).strip()
            if not checksum:
                checksum = hashlib.sha256(
                    f"{name}=={version}".encode("utf-8")
                ).hexdigest()
            if license_name == "UNKNOWN":
                unknown += 1
            if license_name in self.FORBIDDEN_LICENSES:
                forbidden += 1
            normalized.append({
                "name": name,
                "version": version,
                "source": source,
                "license": license_name,
                "checksum": checksum,
            })

        normalized.sort(
            key=lambda item: (
                item["name"].lower(),
                item["version"],
            )
        )
        canonical = json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        checksum = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()
        status = (
            "PASS"
            if forbidden == 0 and unknown == 0
            else "REVIEW"
            if forbidden == 0
            else "BLOCKED"
        )
        return SbomReport(
            report_id=report_id,
            build_version=build_version,
            dependencies=tuple(normalized),
            dependency_count=len(normalized),
            unknown_licenses=unknown,
            forbidden_licenses=forbidden,
            status=status,
            checksum=checksum,
            generated_at=int(
                now if now is not None else time.time()
            ),
        )

    def reproducible_build_report(
        self,
        *,
        report_id: str,
        first_manifest: dict,
        second_manifest: dict,
        now: int | None = None,
    ) -> ReproducibleBuildReport:
        first = hashlib.sha256(
            json.dumps(
                first_manifest,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        second = hashlib.sha256(
            json.dumps(
                second_manifest,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        deterministic = first == second
        return ReproducibleBuildReport(
            report_id=report_id,
            first_manifest_checksum=first,
            second_manifest_checksum=second,
            deterministic=deterministic,
            status="PASS" if deterministic else "FAIL",
            generated_at=int(
                now if now is not None else time.time()
            ),
        )

    def package_integrity_report(
        self,
        *,
        report_id: str,
        package_bytes: bytes,
        expected_checksum: str,
        manifest: dict,
        expected_manifest_checksum: str,
        now: int | None = None,
    ) -> PackageIntegrityReport:
        actual_checksum = hashlib.sha256(
            package_bytes
        ).hexdigest()
        manifest_checksum = hashlib.sha256(
            json.dumps(
                manifest,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        checksum_valid = actual_checksum == expected_checksum
        manifest_valid = (
            manifest_checksum == expected_manifest_checksum
        )
        return PackageIntegrityReport(
            report_id=report_id,
            expected_checksum=expected_checksum,
            actual_checksum=actual_checksum,
            checksum_valid=checksum_valid,
            manifest_checksum=manifest_checksum,
            manifest_valid=manifest_valid,
            status=(
                "PASS"
                if checksum_valid and manifest_valid
                else "FAIL"
            ),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
