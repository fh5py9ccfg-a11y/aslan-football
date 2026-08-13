from __future__ import annotations

import re


_VALID_NAME = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")


class PrometheusExporter:
    def render(self, metrics: dict[str, float]) -> str:
        lines = []
        for name in sorted(metrics):
            if not _VALID_NAME.match(name):
                raise ValueError(f"Geçersiz Prometheus metrik adı: {name}")
            value = metrics[name]
            if not isinstance(value, (int, float)):
                raise TypeError("Metrik değeri sayısal olmalıdır")
            lines.append(f"{name} {float(value)}")
        return "\n".join(lines) + ("\n" if lines else "")
