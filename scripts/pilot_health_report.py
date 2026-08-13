from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen


def main() -> None:
    base_url = os.getenv(
        "ASLAN_BASE_URL",
        "http://localhost:8000",
    ).rstrip("/")
    club_id = os.getenv(
        "ASLAN_CLUB_ID",
        "demo-aslan",
    )
    query = urlencode({
        "report_id": "cli-health-report",
    })
    with urlopen(
        f"{base_url}/mvp/observability/"
        f"{club_id}/health-score?{query}",
        timeout=20,
    ) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
