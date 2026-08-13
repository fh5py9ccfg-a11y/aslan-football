from __future__ import annotations
from dataclasses import dataclass
import time

@dataclass(frozen=True)
class BrokerHealthReport:
    healthy: bool
    latency_ms: float
    error: str | None

class BrokerHealthChecker:
    def check(self, producer, topic: str = "_health") -> BrokerHealthReport:
        started = time.perf_counter()
        try:
            producer.publish(
                topic=topic,
                key="health",
                value={"status": "ping"},
                headers={"x-health-check": "true"},
            )
            latency = (time.perf_counter() - started) * 1000.0
            return BrokerHealthReport(True, latency, None)
        except Exception as exc:
            latency = (time.perf_counter() - started) * 1000.0
            return BrokerHealthReport(False, latency, str(exc))
