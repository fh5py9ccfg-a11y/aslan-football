from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class PipelineStage:
    name: str
    critical: bool
    runner: Callable[[], bool]


@dataclass(frozen=True)
class PipelineStageResult:
    name: str
    passed: bool
    critical: bool
    detail: str


@dataclass(frozen=True)
class PipelineReport:
    passed: bool
    results: tuple[PipelineStageResult, ...]


class DeploymentPipeline:
    def run(self, stages: list[PipelineStage]) -> PipelineReport:
        if not stages:
            raise ValueError("En az bir pipeline aşaması gereklidir")

        results = []
        for stage in stages:
            try:
                passed = bool(stage.runner())
                detail = "ok" if passed else "failed"
            except Exception as exc:
                passed = False
                detail = str(exc)

            results.append(
                PipelineStageResult(
                    name=stage.name,
                    passed=passed,
                    critical=stage.critical,
                    detail=detail,
                )
            )

            if stage.critical and not passed:
                break

        return PipelineReport(
            passed=all(result.passed or not result.critical for result in results),
            results=tuple(results),
        )
