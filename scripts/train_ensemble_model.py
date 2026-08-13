from __future__ import annotations

import argparse
import json
from pathlib import Path

from apps.api.app.ensemble_training import (
    EnsembleTrainingService,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="data/templates/historical_matches.csv",
    )
    parser.add_argument(
        "--competition",
        default="Pilot Lig",
    )
    parser.add_argument(
        "--model-id",
        default="ensemble-v1",
    )
    parser.add_argument(
        "--output",
        default="TRAINED_ENSEMBLE_MODEL.json",
    )
    args = parser.parse_args()

    csv_text = Path(args.csv_file).read_text(
        encoding="utf-8"
    )
    service = EnsembleTrainingService()
    model = service.train(
        model_id=args.model_id,
        csv_text=csv_text,
        competition=args.competition,
    )
    Path(args.output).write_text(
        json.dumps(
            model.__dict__,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(args.output)


if __name__ == "__main__":
    main()
