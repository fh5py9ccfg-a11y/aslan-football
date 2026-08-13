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
        "--minimum-train-size",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--step-size",
        type=int,
        default=5,
    )
    args = parser.parse_args()

    csv_text = Path(args.csv_file).read_text(
        encoding="utf-8"
    )
    report = (
        EnsembleTrainingService()
        .walk_forward_backtest(
            report_id="cli-ensemble-backtest",
            csv_text=csv_text,
            competition=args.competition,
            minimum_train_size=args.minimum_train_size,
            step_size=args.step_size,
        )
    )
    print(
        json.dumps(
            report.__dict__,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
