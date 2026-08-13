from __future__ import annotations

import json
from pathlib import Path

from apps.api.app.ensemble_training import EnsembleTrainingService
from apps.api.app.real_data_training import RealDataTrainingService


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    csv_file = root / "data/templates/historical_matches.csv"
    csv_text = csv_file.read_text(encoding="utf-8")

    baseline = RealDataTrainingService().train_baseline(
        model_id="quick-baseline",
        csv_text=csv_text,
        competition="Pilot Lig",
    )
    ensemble = EnsembleTrainingService().train(
        model_id="quick-ensemble",
        csv_text=csv_text,
        competition="Pilot Lig",
    )

    (root / "QUICK_BASELINE_MODEL.json").write_text(
        json.dumps(baseline.__dict__, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "QUICK_ENSEMBLE_MODEL.json").write_text(
        json.dumps(ensemble.__dict__, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Hazır modeller oluşturuldu:")
    print(root / "QUICK_BASELINE_MODEL.json")
    print(root / "QUICK_ENSEMBLE_MODEL.json")


if __name__ == "__main__":
    main()
