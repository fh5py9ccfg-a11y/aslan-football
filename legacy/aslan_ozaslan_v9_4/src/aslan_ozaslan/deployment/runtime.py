from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeResources:
    cpu_request: float
    cpu_limit: float
    memory_request_mb: int
    memory_limit_mb: int


@dataclass(frozen=True)
class RuntimePolicy:
    replicas: int
    max_unavailable: int
    max_surge: int
    resources: RuntimeResources
    read_only_root_filesystem: bool
    run_as_non_root: bool


class RuntimePolicyValidator:
    def validate(self, policy: RuntimePolicy, *, production: bool) -> tuple[str, ...]:
        errors = []

        if policy.replicas <= 0:
            errors.append("replicas_must_be_positive")
        if production and policy.replicas < 2:
            errors.append("production_requires_two_replicas")
        if policy.max_unavailable < 0 or policy.max_surge < 0:
            errors.append("rolling_update_values_invalid")
        if policy.resources.cpu_request <= 0:
            errors.append("cpu_request_required")
        if policy.resources.cpu_limit < policy.resources.cpu_request:
            errors.append("cpu_limit_below_request")
        if policy.resources.memory_request_mb <= 0:
            errors.append("memory_request_required")
        if policy.resources.memory_limit_mb < policy.resources.memory_request_mb:
            errors.append("memory_limit_below_request")
        if production and not policy.read_only_root_filesystem:
            errors.append("read_only_root_required")
        if production and not policy.run_as_non_root:
            errors.append("non_root_required")

        return tuple(errors)
