from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class RunbookExecution:
    execution_id: str
    incident_code: str
    operator: str
    started_at: str
    completed_steps: tuple[str, ...]
    status: str


class RunbookHistory:
    VALID_STATUSES = {"RUNNING", "SUCCEEDED", "FAILED"}

    def __init__(self):
        self._executions: dict[str, RunbookExecution] = {}

    def start(self, execution_id: str, incident_code: str, operator: str) -> RunbookExecution:
        if not execution_id.strip() or not incident_code.strip() or not operator.strip():
            raise ValueError("Runbook execution alanları boş olamaz")
        if execution_id in self._executions:
            raise ValueError("Execution zaten kayıtlı")

        execution = RunbookExecution(
            execution_id=execution_id,
            incident_code=incident_code,
            operator=operator,
            started_at=datetime.now(timezone.utc).isoformat(),
            completed_steps=(),
            status="RUNNING",
        )
        self._executions[execution_id] = execution
        return execution

    def record_step(self, execution_id: str, step: str) -> RunbookExecution:
        execution = self._require_running(execution_id)
        updated = RunbookExecution(
            execution_id=execution.execution_id,
            incident_code=execution.incident_code,
            operator=execution.operator,
            started_at=execution.started_at,
            completed_steps=execution.completed_steps + (step,),
            status=execution.status,
        )
        self._executions[execution_id] = updated
        return updated

    def finish(self, execution_id: str, status: str) -> RunbookExecution:
        if status not in {"SUCCEEDED", "FAILED"}:
            raise ValueError("Runbook yalnızca SUCCEEDED veya FAILED tamamlanabilir")
        execution = self._require_running(execution_id)
        updated = RunbookExecution(
            execution_id=execution.execution_id,
            incident_code=execution.incident_code,
            operator=execution.operator,
            started_at=execution.started_at,
            completed_steps=execution.completed_steps,
            status=status,
        )
        self._executions[execution_id] = updated
        return updated

    def get(self, execution_id: str) -> RunbookExecution:
        try:
            return self._executions[execution_id]
        except KeyError as exc:
            raise KeyError(f"Execution bulunamadı: {execution_id}") from exc

    def _require_running(self, execution_id: str) -> RunbookExecution:
        execution = self.get(execution_id)
        if execution.status != "RUNNING":
            raise ValueError("Tamamlanmış runbook değiştirilemez")
        return execution
