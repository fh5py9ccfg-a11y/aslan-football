from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class PolicyRule:
    name: str
    severity: str
    evaluator: Callable[[dict[str, Any]], bool]
    message: str


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


class PolicyEngine:
    def evaluate(self, context: dict[str, Any], rules: list[PolicyRule]) -> PolicyDecision:
        blockers = []
        warnings = []

        for rule in rules:
            try:
                passed = bool(rule.evaluator(context))
            except Exception:
                passed = False

            if passed:
                continue

            item = f"{rule.name}:{rule.message}"
            severity = rule.severity.upper()
            if severity == "BLOCKER":
                blockers.append(item)
            else:
                warnings.append(item)

        return PolicyDecision(
            allowed=not blockers,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
        )
