from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PostgresAuditContract:
    table_name: str
    insert_sql: str
    verify_sql: str
    protections: tuple[str, ...]


def build_postgres_audit_contract() -> PostgresAuditContract:
    return PostgresAuditContract(
        table_name="immutable_audit_records",
        insert_sql=(
            "INSERT INTO immutable_audit_records "
            "(audit_id, actor_id, action, resource_type, resource_id, payload_json, "
            "created_at, previous_hash, record_hash) "
            "VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)"
        ),
        verify_sql=(
            "SELECT sequence_id, previous_hash, record_hash "
            "FROM immutable_audit_records ORDER BY sequence_id ASC"
        ),
        protections=(
            "revoke-update",
            "revoke-delete",
            "append-only-role",
            "row-level-security",
            "periodic-chain-verification",
            "worm-export",
        ),
    )
