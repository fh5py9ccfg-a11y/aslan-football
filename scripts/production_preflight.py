from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen


def main() -> int:
    base_url = os.getenv(
        "ASLAN_BASE_URL",
        "http://localhost:8000",
    ).rstrip("/")
    query = urlencode({
        "report_id": "cli-production-preflight",
        "database_ready": "true",
        "redis_ready": "true",
        "backup_ready": "true",
        "observability_ready": "true",
    })
    with urlopen(
        f"{base_url}/mvp/release-freeze/preflight?{query}",
        timeout=30,
    ) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
