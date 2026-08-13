from __future__ import annotations

import concurrent.futures
import json
import os
import statistics
import time
from urllib.request import urlopen


def request(url: str) -> float:
    started = time.perf_counter()
    with urlopen(url, timeout=10) as response:
        response.read()
        if response.status != 200:
            raise RuntimeError(
                f"HTTP {response.status}"
            )
    return (
        time.perf_counter() - started
    ) * 1000


def main() -> int:
    base_url = os.getenv(
        "ASLAN_BASE_URL",
        "http://localhost:8000",
    ).rstrip("/")
    requests = int(
        os.getenv("LOAD_PROBE_REQUESTS", "100")
    )
    concurrency = int(
        os.getenv("LOAD_PROBE_CONCURRENCY", "10")
    )
    url = f"{base_url}/health"

    failures = 0
    durations = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:
        futures = [
            executor.submit(request, url)
            for _ in range(requests)
        ]
        for future in futures:
            try:
                durations.append(future.result())
            except Exception:
                failures += 1

    durations.sort()
    p95_index = max(
        0,
        min(
            len(durations) - 1,
            int(len(durations) * 0.95) - 1,
        ),
    )
    report = {
        "requests": requests,
        "successes": len(durations),
        "failures": failures,
        "mean_ms": (
            round(statistics.mean(durations), 2)
            if durations
            else None
        ),
        "p95_ms": (
            round(durations[p95_index], 2)
            if durations
            else None
        ),
        "pass": (
            failures == 0
            and bool(durations)
            and durations[p95_index] < 500
        ),
    }
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
