from __future__ import annotations
from dataclasses import dataclass
import time

@dataclass(frozen=True)
class SmokeCheck:
    name: str
    passed: bool
    latency_ms: float
    detail: str

@dataclass(frozen=True)
class SmokeTestReport:
    passed: bool
    checks: tuple[SmokeCheck, ...]
    provider_verified: bool

class ProductionSmokeTestRunner:
    def __init__(self, *, sportmonks_client, event_store, decision_engine):
        self.sportmonks_client = sportmonks_client
        self.event_store = event_store
        self.decision_engine = decision_engine

    def run(self, *, fixture_id: int | None = None) -> SmokeTestReport:
        checks = []

        started = time.perf_counter()
        try:
            self.sportmonks_client.config.validate()
            connected = self.sportmonks_client.config.connected
            checks.append(SmokeCheck(
                name="provider_config",
                passed=connected,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                detail="token_available" if connected else "token_missing",
            ))
        except Exception as exc:
            checks.append(SmokeCheck(
                name="provider_config",
                passed=False,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                detail=str(exc),
            ))

        provider_verified = False
        if fixture_id is not None and checks[-1].passed:
            started = time.perf_counter()
            try:
                fixture = self.sportmonks_client.fixture_by_id(fixture_id)
                provider_verified = bool(fixture.get("id"))
                checks.append(SmokeCheck(
                    name="provider_fixture_fetch",
                    passed=provider_verified,
                    latency_ms=(time.perf_counter() - started) * 1000.0,
                    detail="fixture_received" if provider_verified else "fixture_missing",
                ))
            except Exception as exc:
                checks.append(SmokeCheck(
                    name="provider_fixture_fetch",
                    passed=False,
                    latency_ms=(time.perf_counter() - started) * 1000.0,
                    detail=str(exc),
                ))
        else:
            checks.append(SmokeCheck(
                name="provider_fixture_fetch",
                passed=False,
                latency_ms=0.0,
                detail="fixture_id_or_token_missing",
            ))

        started = time.perf_counter()
        try:
            store_ready = self.event_store is not None
            checks.append(SmokeCheck(
                name="event_store",
                passed=store_ready,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                detail="ready" if store_ready else "missing",
            ))
        except Exception as exc:
            checks.append(SmokeCheck(
                name="event_store",
                passed=False,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                detail=str(exc),
            ))

        started = time.perf_counter()
        engine_ready = self.decision_engine is not None
        checks.append(SmokeCheck(
            name="decision_engine",
            passed=engine_ready,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            detail="ready" if engine_ready else "missing",
        ))

        return SmokeTestReport(
            passed=all(check.passed for check in checks),
            checks=tuple(checks),
            provider_verified=provider_verified,
        )
