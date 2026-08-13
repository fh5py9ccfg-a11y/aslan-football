from __future__ import annotations

import argparse
import json
from pathlib import Path

from apps.api.app.rolling_team_model import (
    RollingTeamModelService,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    parser.add_argument("--competition", required=True)
    parser.add_argument(
        "--model-id",
        default="rolling-logistic-v1",
    )
    parser.add_argument(
        "--output",
        default="TRAINED_ROLLING_MODEL.json",
    )
    args = parser.parse_args()

    csv_text = Path(args.csv_file).read_text(
        encoding="utf-8"
    )
    model = RollingTeamModelService().train(
        model_id=args.model_id,
        csv_text=csv_text,
        competition=args.competition,
    )
    payload = {
        **model.__dict__,
        "feature_names": list(model.feature_names),
        "means": list(model.means),
        "scales": list(model.scales),
        "weights": [list(row) for row in model.weights],
        "biases": list(model.biases),
    }
    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(args.output)


if __name__ == "__main__":
    main()
