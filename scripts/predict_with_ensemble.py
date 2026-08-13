from __future__ import annotations

import argparse
import json
from pathlib import Path

from apps.api.app.ensemble_training import (
    EnsembleModel,
    EnsembleTrainingService,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="TRAINED_ENSEMBLE_MODEL.json",
    )
    parser.add_argument("--home-xg", type=float, required=True)
    parser.add_argument("--away-xg", type=float, required=True)
    parser.add_argument("--home-elo", type=float, required=True)
    parser.add_argument("--away-elo", type=float, required=True)
    parser.add_argument("--home-form", type=float, default=0.5)
    parser.add_argument("--away-form", type=float, default=0.5)
    args = parser.parse_args()

    model = EnsembleModel(
        **json.loads(
            Path(args.model).read_text(encoding="utf-8")
        )
    )
    prediction = EnsembleTrainingService().predict(
        model=model,
        home_xg=args.home_xg,
        away_xg=args.away_xg,
        home_elo=args.home_elo,
        away_elo=args.away_elo,
        home_form=args.home_form,
        away_form=args.away_form,
    )
    print(
        json.dumps(
            prediction,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
