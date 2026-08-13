from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Counter:
    name: str
    value: int = 0

    def increment(self, amount: int = 1) -> None:
        if amount < 0:
            raise ValueError("Counter negatif artırılamaz")
        self.value += amount


@dataclass
class Gauge:
    name: str
    value: float = 0.0

    def set(self, value: float) -> None:
        self.value = float(value)


class MetricsRegistry:
    def __init__(self):
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}

    def counter(self, name: str) -> Counter:
        if name not in self._counters:
            self._counters[name] = Counter(name)
        return self._counters[name]

    def gauge(self, name: str) -> Gauge:
        if name not in self._gauges:
            self._gauges[name] = Gauge(name)
        return self._gauges[name]

    def snapshot(self) -> dict[str, float]:
        values = {name: counter.value for name, counter in self._counters.items()}
        values.update({name: gauge.value for name, gauge in self._gauges.items()})
        return values
