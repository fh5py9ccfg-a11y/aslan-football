from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class FeatureTimestamp:
    feature_name: str
    available_at: datetime

@dataclass(frozen=True)
class LeakageReport:
    safe: bool
    leaked_features: tuple[str, ...]

class DataLeakageGuard:
    def evaluate(
        self,
        *,
        prediction_time: datetime,
        features: list[FeatureTimestamp],
    ) -> LeakageReport:
        if prediction_time.tzinfo is None:
            raise ValueError("prediction_time timezone içermelidir")

        leaked = []
        for feature in features:
            if feature.available_at.tzinfo is None:
                raise ValueError("Feature zamanları timezone içermelidir")
            if feature.available_at > prediction_time:
                leaked.append(feature.feature_name)

        return LeakageReport(
            safe=not leaked,
            leaked_features=tuple(sorted(set(leaked))),
        )
