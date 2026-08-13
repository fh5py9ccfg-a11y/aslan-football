import asyncio

from apps.api.app.self_healing_worker import SelfHealingWorker


class Orchestrator:
    def reconcile(self):
        return ("action",)


def test_worker_runs_reconcile_cycle():
    worker = SelfHealingWorker(
        orchestrator=Orchestrator(),
        interval_seconds=10,
    )
    result = asyncio.run(worker.run_once())
    assert result == ("action",)
    assert worker.last_actions == ("action",)
