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
    parser.add_argument("--home-team", default="Ev Sahibi")
    parser.add_argument("--away-team", default="Deplasman")
    parser.add_argument("--home-xg", type=float, required=True)
    parser.add_argument("--away-xg", type=float, required=True)
    parser.add_argument("--home-elo", type=float, required=True)
    parser.add_argument("--away-elo", type=float, required=True)
    parser.add_argument("--home-form", type=float, default=0.5)
    parser.add_argument("--away-form", type=float, default=0.5)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    model_path = root / "QUICK_ENSEMBLE_MODEL.json"

    if not model_path.exists():
        raise SystemExit(
            "Önce `python scripts/quick_train.py` çalıştırın."
        )

    model = EnsembleModel(
        **json.loads(model_path.read_text(encoding="utf-8"))
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

    result = {
        "match": f"{args.home_team} - {args.away_team}",
        **prediction,
        "warning": "Bu çıktı olasılık tahminidir; kesin sonuç değildir.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
