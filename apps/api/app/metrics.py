from __future__ import annotations
from collections import defaultdict
from threading import Lock

class MetricsRegistry:
    def __init__(self):
        self._counters = defaultdict(float)
        self._lock = Lock()

    def increment(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self._counters[name] += value

    def render(self) -> str:
        with self._lock:
            lines = []
            for name, value in sorted(self._counters.items()):
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")
            return "\n".join(lines) + ("\n" if lines else "")

metrics = MetricsRegistry()
