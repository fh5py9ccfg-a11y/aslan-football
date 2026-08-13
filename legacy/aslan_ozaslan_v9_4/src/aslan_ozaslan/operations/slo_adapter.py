from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SLOMeasurement:
    name: str
    achieved: float
    window_days: int
    source: str


class SLODataSource(Protocol):
    name: str

    def measure(self, objective_name: str, window_days: int) -> SLOMeasurement:
        ...


class SLOMeasurementService:
    def __init__(self, source: SLODataSource):
        self.source = source

    def collect(self, objective_name: str, window_days: int) -> SLOMeasurement:
        if not objective_name.strip():
            raise ValueError("Objective adı boş olamaz")
        if window_days <= 0:
            raise ValueError("window_days pozitif olmalıdır")

        measurement = self.source.measure(objective_name, window_days)
        if measurement.source != self.source.name:
            raise ValueError("SLO veri kaynağı kimliği uyuşmuyor")
        if measurement.name != objective_name:
            raise ValueError("SLO objective adı uyuşmuyor")
        if measurement.window_days != window_days:
            raise ValueError("SLO ölçüm penceresi uyuşmuyor")
        if not 0 <= measurement.achieved <= 1:
            raise ValueError("SLO ölçümü 0 ile 1 arasında olmalıdır")
        return measurement
