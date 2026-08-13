from __future__ import annotations

import argparse
import json
from pathlib import Path

from apps.api.app.rolling_team_model import (
    RollingModel,
    RollingTeamModelService,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="TRAINED_ROLLING_MODEL.json",
    )
    parser.add_argument(
        "--features",
        required=True,
        help="Virgülle ayrılmış 11 özellik",
    )
    args = parser.parse_args()

    data = json.loads(
        Path(args.model).read_text(encoding="utf-8")
    )
    data["feature_names"] = tuple(data["feature_names"])
    data["means"] = tuple(data["means"])
    data["scales"] = tuple(data["scales"])
    data["weights"] = tuple(
        tuple(row) for row in data["weights"]
    )
    data["biases"] = tuple(data["biases"])
    model = RollingModel(**data)

    features = tuple(
        float(value.strip())
        for value in args.features.split(",")
    )
    if len(features) != 11:
        raise SystemExit("Tam olarak 11 özellik girilmelidir")

    prediction = (
        RollingTeamModelService()
        .predict_from_features(
            model=model,
            features=features,
        )
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
