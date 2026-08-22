from contextlib import asynccontextmanager
import logging
import os

from .audit import (
    InMemoryAuditRepository,
    JsonAuditRepository,
    PostgresAuditRepository,
)

logger = logging.getLogger(__name__)


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


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _log_comeback_startup_diagnostic() -> None:
    """Emit one compact, failure-tolerant startup line for Render logs."""
    environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "")).strip().lower()
    if environment == "test" or os.getenv("PYTEST_CURRENT_TEST"):
        return
    if not _env_bool("COMEBACK_STARTUP_DIAGNOSTIC", True):
        return

    try:
        from datetime import datetime, timedelta, timezone

        from .comeback_backtest import run_comeback_backtest
        from .comeback_calibration import calibrate_thresholds
        from .comeback_fixture_adapter import (
            comeback_data_readiness,
            load_comeback_fixtures,
        )

        lookback_days = int(os.getenv("COMEBACK_BACKTEST_LOOKBACK_DAYS", "1460"))
        min_matches = int(os.getenv("COMEBACK_BACKTEST_MIN_MATCHES", "100"))
        window_hours = int(os.getenv("COMEBACK_LIVE_WINDOW_HOURS", "36"))

        backtest = run_comeback_backtest(
            lookback_days=lookback_days,
            min_matches=min_matches,
        )
        calibration = calibrate_thresholds(backtest)

        start = datetime.now(timezone.utc)
        fixtures = load_comeback_fixtures(
            start=start,
            end=start + timedelta(hours=window_hours),
            limit=2000,
        )
        readiness = comeback_data_readiness(fixtures)

        t21 = int(calibration["2/1"]["threshold"])
        t12 = int(calibration["1/2"]["threshold"])
        eligible = int(backtest.get("eligible_matches", 0))
        enough = bool(backtest.get("enough_data"))
        ready = int(readiness.get("ready", 0))
        history_ready = int(readiness.get("history_ready", 0))
        direct_htft = int(readiness.get("direct_htft_ready", 0))
        total = int(readiness.get("fixtures", 0))
        live_ready = enough and ready > 0

        logger.info(
            "COMEBACK_SELF_CHECK ready=%s eligible=%s/%s thresholds=2/1:%s,1/2:%s "
            "fixtures_ready=%s/%s history_ready=%s direct_htft=%s",
            "YES" if live_ready else "NO",
            eligible,
            min_matches,
            t21,
            t12,
            ready,
            total,
            history_ready,
            direct_htft,
        )
    except Exception as exc:
        # Diagnostics must never block API startup.
        logger.warning(
            "COMEBACK_SELF_CHECK failed error=%s",
            str(exc)[:400],
        )


@asynccontextmanager
async def lifespan(app):
    app.state.shutting_down = False

    # Mount optional feature routers once the FastAPI app exists. Keeping this
    # here avoids coupling the large main.py module to isolated prediction
    # features and keeps startup backwards-compatible.
    if not getattr(app.state, "comeback_routes_mounted", False):
        from .comeback_routes import router as comeback_router
        app.include_router(comeback_router)
        app.state.comeback_routes_mounted = True

    _log_comeback_startup_diagnostic()

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
