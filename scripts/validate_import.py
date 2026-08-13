from __future__ import annotations

import argparse
import json
from pathlib import Path

from apps.api.app.delivery_hardening import (
    DeliveryHardeningService,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("import_type", choices=("PLAYERS", "MATCHES"))
    parser.add_argument("csv_file")
    parser.add_argument(
        "--quarantine",
        default="quarantine.json",
    )
    args = parser.parse_args()

    csv_text = Path(args.csv_file).read_text(
        encoding="utf-8"
    )
    report = DeliveryHardeningService().validate_csv(
        report_id="cli-import-validation",
        import_type=args.import_type,
        csv_text=csv_text,
    )
    payload = {
        **report.__dict__,
        "valid_payload": list(report.valid_payload),
        "quarantine_payload": list(
            report.quarantine_payload
        ),
        "issues": list(report.issues),
    }
    Path(args.quarantine).write_text(
        json.dumps(
            {
                "invalid_rows": payload["quarantine_payload"],
                "issues": payload["issues"],
                "checksum": payload["checksum"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if report.invalid_rows == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
