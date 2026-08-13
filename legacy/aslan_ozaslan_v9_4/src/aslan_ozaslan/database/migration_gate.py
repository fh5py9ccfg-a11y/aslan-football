from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    reversible: bool
    checksum: str


@dataclass(frozen=True)
class MigrationGateReport:
    allowed: bool
    blockers: tuple[str, ...]


class MigrationGate:
    def evaluate(
        self,
        *,
        applied_versions: set[int],
        pending: list[Migration],
        production: bool,
    ) -> MigrationGateReport:
        blockers = []

        versions = [migration.version for migration in pending]
        if len(versions) != len(set(versions)):
            blockers.append("duplicate_migration_version")

        for migration in pending:
            if migration.version in applied_versions:
                blockers.append(f"already_applied:{migration.version}")
            if not migration.checksum.strip():
                blockers.append(f"missing_checksum:{migration.version}")
            if production and not migration.reversible:
                blockers.append(f"irreversible_in_production:{migration.version}")

        if versions != sorted(versions):
            blockers.append("migration_order_invalid")

        return MigrationGateReport(
            allowed=not blockers,
            blockers=tuple(blockers),
        )
