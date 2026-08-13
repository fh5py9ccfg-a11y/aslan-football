from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelCandidate:
    name: str
    accuracy: float
    brier_score: float
    log_loss: float
    calibration_error: float

@dataclass(frozen=True)
class ModelComparison:
    champion: str
    reason: str
    ranking: tuple[str, ...]

def compare_models(candidates: list[ModelCandidate]) -> ModelComparison:
    if not candidates:
        raise ValueError("En az bir model adayı gereklidir")

    for candidate in candidates:
        if not (0 <= candidate.accuracy <= 1):
            raise ValueError("accuracy 0 ile 1 arasında olmalıdır")
        if candidate.brier_score < 0 or candidate.log_loss < 0 or candidate.calibration_error < 0:
            raise ValueError("Hata ölçütleri negatif olamaz")

    ranked = sorted(
        candidates,
        key=lambda item: (
            item.log_loss,
            item.brier_score,
            item.calibration_error,
            -item.accuracy,
            item.name,
        ),
    )
    winner = ranked[0]
    return ModelComparison(
        champion=winner.name,
        reason=(
            "En düşük log-loss önceliklendirildi; eşitlikte Brier score, "
            "kalibrasyon hatası ve accuracy kullanıldı."
        ),
        ranking=tuple(item.name for item in ranked),
    )
