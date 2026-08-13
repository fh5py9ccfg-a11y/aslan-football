from contextlib import asynccontextmanager
import os

from .audit import (
    InMemoryAuditRepository,
    JsonAuditRepository,
    PostgresAuditRepository,
)

def build_audit_repository(environment):
    if environment == "test":
        return InMemoryAuditRepository()

    backend = os.getenv(
        "AUDIT_BACKEND",
        "postgres",
    ).lower()

    if backend == "json":
        return JsonAuditRepository(
            os.getenv(
                "AUDIT_LOG_PATH",
                "/data/audit.json",
            )
        )

    from .db import SessionLocal
    return PostgresAuditRepository(
        SessionLocal
    )

@asynccontextmanager
async def lifespan(app):
    app.state.shutting_down = False
    refresher = getattr(
        app.state,
        'oidc_metadata_refresher',
        None,
    )
    if refresher is not None:
        await refresher.start()

    maintenance_worker = getattr(
        app.state,
        'session_maintenance_worker',
        None,
    )
    if maintenance_worker is not None:
        await maintenance_worker.start()

    compensation_worker = getattr(
        app.state,
        'compensation_worker',
        None,
    )
    if compensation_worker is not None:
        await compensation_worker.start()

    outbox_publisher_worker = getattr(
        app.state,
        'outbox_publisher_worker',
        None,
    )
    if outbox_publisher_worker is not None:
        await outbox_publisher_worker.start()

    self_healing_worker = getattr(
        app.state,
        "self_healing_worker",
        None,
    )
    if self_healing_worker is not None:
        await self_healing_worker.start()

    yield
    app.state.drain_controller.enter(
        reason='graceful shutdown',
    )
    app.state.shutting_down = True
    if self_healing_worker is not None:
        await self_healing_worker.stop()
    if refresher is not None:
        await refresher.stop()
    if maintenance_worker is not None:
        await maintenance_worker.stop()
    if compensation_worker is not None:
        await compensation_worker.stop()
    if outbox_publisher_worker is not None:
        await outbox_publisher_worker.stop()

    discovery_cache = getattr(
        app.state,
        'oidc_discovery_cache',
        None,
    )
    if discovery_cache is not None:
        discovery_cache.close()

    jwks_cache = getattr(app.state, 'oidc_jwks_cache', None)
    if jwks_cache is not None:
        jwks_cache.close()

    redis_client = getattr(
        app.state.rate_limiter,
        "client",
        None,
    )
    if redis_client is not None:
        close = getattr(
            redis_client,
            "close",
            None,
        )
        if callable(close):
            close()
