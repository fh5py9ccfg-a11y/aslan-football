from __future__ import annotations

from dataclasses import dataclass

from .gatekeeper import GatekeeperConstraint


@dataclass(frozen=True)
class ConstraintSet:
    constraints: tuple[GatekeeperConstraint, ...]


class ProductionConstraintSetFactory:
    def build(self) -> ConstraintSet:
        return ConstraintSet(
            constraints=(
                GatekeeperConstraint(
                    name="require-image-digest",
                    kind="K8sImmutableImage",
                    message="image digest zorunlu",
                    parameters={},
                ),
                GatekeeperConstraint(
                    name="require-non-root",
                    kind="K8sRequireNonRoot",
                    message="container non-root çalışmalıdır",
                    parameters={},
                ),
                GatekeeperConstraint(
                    name="require-read-only-root",
                    kind="K8sReadOnlyRoot",
                    message="root filesystem read-only olmalıdır",
                    parameters={},
                ),
                GatekeeperConstraint(
                    name="require-resource-limits",
                    kind="K8sResourceLimits",
                    message="CPU ve bellek limitleri zorunludur",
                    parameters={},
                ),
                GatekeeperConstraint(
                    name="require-probes",
                    kind="K8sHealthProbes",
                    message="readiness ve liveness probe zorunludur",
                    parameters={},
                ),
            )
        )
