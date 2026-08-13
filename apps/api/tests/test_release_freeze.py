import hashlib
import json
import pytest

from apps.api.app.release_freeze import (
    ReleaseFreezeService,
    ReleaseFreezeValidationError,
)


def test_production_preflight_passes_with_secure_env():
    service = ReleaseFreezeService()
    env = {
        "APP_ENV": "production",
        "AUTH_TOKEN_SECRET": "x" * 32,
        "JWT_ACTIVE_KID": "kid-1",
        "JWT_ISSUER": "aslan",
        "JWT_AUDIENCE": "pilot",
        "MVP_AUTH_SECRET": "y" * 32,
    }

    report = service.production_preflight(
        report_id="r1",
        database_ready=True,
        redis_ready=True,
        backup_ready=True,
        observability_ready=True,
        environment=env,
        now=100,
    )

    assert report.status == "PASS"
    assert report.missing_variables == ()
    assert report.insecure_variables == ()


def test_migration_blocks_removed_fields():
    service = ReleaseFreezeService()
    report = service.migration_preflight(
        report_id="m1",
        source_schema="v1",
        target_schema="v2",
        source_fields=("id", "name", "age"),
        target_fields=("id", "name"),
        now=100,
    )

    assert report.status == "BLOCKED"
    assert report.compatible is False
    assert len(report.destructive_changes) == 1


def test_disaster_recovery_and_signature():
    service = ReleaseFreezeService()
    payload = json.dumps({
        "schema_version": "build-022",
        "club": {},
        "players": [],
        "matches": [],
    })
    checksum = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()
    drill = service.disaster_recovery_drill(
        report_id="d1",
        backup_payload=payload,
        expected_checksum=checksum,
        required_sections=("club", "players", "matches"),
        recovery_time_objective_minutes=30,
        recovery_point_objective_minutes=60,
        smoke_test_ready=True,
        now=100,
    )
    signed = service.sign_release(
        manifest_id="s1",
        build_version="build-023",
        package_checksum="a" * 64,
        source_manifest_checksum="b" * 64,
        acceptance_fingerprint="c" * 64,
        signing_key="release-signing-key-123456789",
        now=100,
    )

    assert drill.status == "PASS"
    assert len(signed.signature) == 64
    assert signed.immutable is True


def test_short_signing_key_rejected():
    service = ReleaseFreezeService()

    with pytest.raises(ReleaseFreezeValidationError):
        service.sign_release(
            manifest_id="s1",
            build_version="build-023",
            package_checksum="a",
            source_manifest_checksum="b",
            acceptance_fingerprint="c",
            signing_key="short",
            now=100,
        )
