from __future__ import annotations
from collections import deque

from .domain import DecisionQualitySample

class DecisionQualityWindow:
    def __init__(self, capacity: int = 200):
        if capacity <= 0:
            raise ValueError("capacity pozitif olmalıdır")
        self.capacity = capacity
        self._samples = deque(maxlen=capacity)

    def add(self, sample: DecisionQualitySample) -> None:
        sample.validate()
        self._samples.append(sample)

    def samples(self) -> tuple[DecisionQualitySample, ...]:
        return tuple(self._samples)

    def __len__(self) -> int:
        return len(self._samples)
