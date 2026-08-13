import asyncio
import time

from apps.api.app.compensation_orchestrator import (
    CompensationHandlerRegistry,
    CompensationOrchestrator,
)

class Record:
    compensation_id = "c1"
    request_id = "r1"
    claim_id = "q1"
    action = "ACTION"
    status = "PENDING"
    reason = ""
    attempts = 0
    completed_at = None
    next_attempt_at = 0

class Repo:
    def __init__(self):
        self.record = Record()
    def get(self, compensation_id):
        return self.record

class Execution:
    status = "IN_PROGRESS"
    owner_token = "token"

class ExecRepo:
    def claim(self, **kwargs):
        return True, Execution()
    def heartbeat(self, record):
        return record

class Committer:
    def __init__(self, repo):
        self.repo = repo
        self.calls = 0
    def commit_success(self, **kwargs):
        self.calls += 1
        self.repo.record.status = "COMPLETED"
        self.repo.record.attempts = 1
        self.repo.record.completed_at = 100

def test_orchestrator_uses_atomic_committer():
    repo = Repo()
    committer = Committer(repo)
    registry = CompensationHandlerRegistry()
    registry.register("ACTION", lambda record: None)

    orchestrator = CompensationOrchestrator(
        repository=repo,
        registry=registry,
        execution_repository=ExecRepo(),
        heartbeat_interval_seconds=0.01,
        atomic_committer=committer,
    )

    result = asyncio.run(orchestrator.execute_async("c1", now=100))
    assert result.status == "COMPLETED"
    assert committer.calls == 1
