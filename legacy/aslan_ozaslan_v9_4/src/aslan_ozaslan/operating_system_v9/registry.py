from __future__ import annotations

class ExpertRegistry:
    def __init__(self):
        self._experts = {}

    def register(self, name: str, expert) -> None:
        if not name.strip():
            raise ValueError("Uzman adı boş olamaz")
        if name in self._experts:
            raise ValueError(f"Uzman zaten kayıtlı: {name}")
        self._experts[name] = expert

    def get(self, name: str):
        if name not in self._experts:
            raise KeyError(f"Uzman bulunamadı: {name}")
        return self._experts[name]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._experts))

    def evaluate_all(self, context) -> tuple:
        decisions = []
        for name in self.names():
            result = self._experts[name].evaluate(context)
            result.validate()
            decisions.append(result)
        return tuple(decisions)
