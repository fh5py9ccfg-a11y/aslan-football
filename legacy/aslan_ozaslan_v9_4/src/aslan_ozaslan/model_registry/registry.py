from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class ModelVersion:
    version: str
    status: str
    trained_until: str
    log_loss: float
    brier_score: float
    calibration_error: float
    created_at: str

class ModelRegistry:
    VALID_STATUSES = {"CANDIDATE","CHAMPION","RETIRED"}

    def __init__(self):
        self._versions = {}

    def register(self, *, version, status, trained_until, log_loss, brier_score, calibration_error):
        if status not in self.VALID_STATUSES:
            raise ValueError("Geçersiz model durumu")
        if version in self._versions:
            raise ValueError("Model sürümü zaten kayıtlı")
        if min(log_loss,brier_score,calibration_error) < 0:
            raise ValueError("Ölçütler negatif olamaz")
        if status == "CHAMPION":
            for key, record in list(self._versions.items()):
                if record.status == "CHAMPION":
                    self._versions[key] = ModelVersion(
                        record.version,"RETIRED",record.trained_until,
                        record.log_loss,record.brier_score,
                        record.calibration_error,record.created_at
                    )
        record = ModelVersion(
            version,status,trained_until,log_loss,brier_score,
            calibration_error,datetime.now(timezone.utc).isoformat()
        )
        self._versions[version] = record
        return record

    def champion(self):
        return next((r for r in self._versions.values() if r.status == "CHAMPION"), None)
