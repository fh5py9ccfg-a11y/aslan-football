from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
import json
import time


@dataclass(frozen=True)
class ImportValidationIssue:
    row_number: int
    code: str
    message: str
    raw: dict


@dataclass(frozen=True)
class ImportValidationReport:
    report_id: str
    import_type: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    valid_payload: tuple[dict, ...]
    quarantine_payload: tuple[dict, ...]
    issues: tuple[dict, ...]
    checksum: str
    generated_at: int


@dataclass(frozen=True)
class DeliveryManifest:
    manifest_id: str
    build_version: str
    project_name: str
    files_count: int
    tests_passed: int
    tests_deselected: int
    documentation_files: tuple[str, ...]
    operational_scripts: tuple[str, ...]
    package_checksum: str
    acceptance_status: str
    created_at: int


class DeliveryHardeningValidationError(ValueError):
    pass


class DeliveryHardeningService:
    PLAYER_REQUIRED = (
        "player_id",
        "name",
        "position",
        "age",
        "market_value",
    )
    MATCH_REQUIRED = (
        "match_id",
        "opponent",
        "competition",
        "kickoff_at",
        "venue",
    )
    POSITIONS = {
        "GK", "RB", "CB", "LB", "DM",
        "CM", "AM", "RW", "LW", "ST",
    }
    VENUES = {"HOME", "AWAY", "NEUTRAL"}

    def validate_csv(
        self,
        *,
        report_id: str,
        import_type: str,
        csv_text: str,
        now: int | None = None,
    ) -> ImportValidationReport:
        normalized = import_type.upper()
        if normalized not in {"PLAYERS", "MATCHES"}:
            raise DeliveryHardeningValidationError(
                "Import türü PLAYERS veya MATCHES olmalıdır"
            )
        reader = csv.DictReader(io.StringIO(csv_text))
        required = (
            self.PLAYER_REQUIRED
            if normalized == "PLAYERS"
            else self.MATCH_REQUIRED
        )
        missing_headers = [
            header
            for header in required
            if header not in (reader.fieldnames or [])
        ]
        if missing_headers:
            raise DeliveryHardeningValidationError(
                "Eksik CSV başlıkları: "
                + ", ".join(missing_headers)
            )

        valid = []
        quarantine = []
        issues = []

        for row_number, row in enumerate(reader, start=2):
            cleaned = {
                key: (value or "").strip()
                for key, value in row.items()
            }
            row_issues = (
                self._validate_player_row(row_number, cleaned)
                if normalized == "PLAYERS"
                else self._validate_match_row(row_number, cleaned)
            )
            if row_issues:
                quarantine.append({
                    "row_number": row_number,
                    "raw": cleaned,
                })
                issues.extend(row_issues)
            else:
                valid.append(cleaned)

        canonical = json.dumps(
            {
                "import_type": normalized,
                "valid": valid,
                "quarantine": quarantine,
                "issues": issues,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        checksum = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return ImportValidationReport(
            report_id=report_id,
            import_type=normalized,
            total_rows=len(valid) + len(quarantine),
            valid_rows=len(valid),
            invalid_rows=len(quarantine),
            valid_payload=tuple(valid),
            quarantine_payload=tuple(quarantine),
            issues=tuple(issues),
            checksum=checksum,
            generated_at=int(
                now if now is not None else time.time()
            ),
        )

    def _validate_player_row(
        self,
        row_number: int,
        row: dict,
    ) -> list[dict]:
        issues = []
        for field in self.PLAYER_REQUIRED:
            if not row.get(field):
                issues.append({
                    "row_number": row_number,
                    "code": "REQUIRED",
                    "message": f"{field} zorunlu",
                    "raw": row,
                })
        if row.get("position") and row["position"].upper() not in self.POSITIONS:
            issues.append({
                "row_number": row_number,
                "code": "POSITION",
                "message": "Geçersiz pozisyon",
                "raw": row,
            })
        try:
            age = int(row.get("age", ""))
            if not 15 <= age <= 50:
                raise ValueError
        except ValueError:
            issues.append({
                "row_number": row_number,
                "code": "AGE",
                "message": "Yaş 15 ile 50 arasında olmalı",
                "raw": row,
            })
        try:
            value = float(row.get("market_value", ""))
            if value < 0:
                raise ValueError
        except ValueError:
            issues.append({
                "row_number": row_number,
                "code": "MARKET_VALUE",
                "message": "Piyasa değeri negatif olamaz",
                "raw": row,
            })
        return issues

    def _validate_match_row(
        self,
        row_number: int,
        row: dict,
    ) -> list[dict]:
        issues = []
        for field in self.MATCH_REQUIRED:
            if not row.get(field):
                issues.append({
                    "row_number": row_number,
                    "code": "REQUIRED",
                    "message": f"{field} zorunlu",
                    "raw": row,
                })
        if row.get("venue") and row["venue"].upper() not in self.VENUES:
            issues.append({
                "row_number": row_number,
                "code": "VENUE",
                "message": "Geçersiz saha türü",
                "raw": row,
            })
        try:
            kickoff = int(row.get("kickoff_at", ""))
            if kickoff <= 0:
                raise ValueError
        except ValueError:
            issues.append({
                "row_number": row_number,
                "code": "KICKOFF",
                "message": "kickoff_at pozitif Unix zamanı olmalı",
                "raw": row,
            })
        return issues

    def delivery_manifest(
        self,
        *,
        manifest_id: str,
        build_version: str,
        project_name: str,
        files_count: int,
        tests_passed: int,
        tests_deselected: int,
        documentation_files: tuple[str, ...],
        operational_scripts: tuple[str, ...],
        package_checksum: str,
        acceptance_status: str,
        now: int | None = None,
    ) -> DeliveryManifest:
        return DeliveryManifest(
            manifest_id=manifest_id,
            build_version=build_version,
            project_name=project_name,
            files_count=files_count,
            tests_passed=tests_passed,
            tests_deselected=tests_deselected,
            documentation_files=tuple(sorted(documentation_files)),
            operational_scripts=tuple(sorted(operational_scripts)),
            package_checksum=package_checksum,
            acceptance_status=acceptance_status,
            created_at=int(
                now if now is not None else time.time()
            ),
        )
