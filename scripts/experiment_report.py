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
    experiment_id = os.getenv(
        "ASLAN_EXPERIMENT_ID",
        "pilot-experiment",
    )
    query = urlencode({
        "report_id": "cli-experiment-report",
    })
    with urlopen(
        f"{base_url}/mvp/experiments/"
        f"{experiment_id}/report?{query}",
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
