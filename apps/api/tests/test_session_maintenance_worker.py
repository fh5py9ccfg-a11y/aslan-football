import asyncio

from apps.api.app.session_maintenance import (
    SessionIndexMaintenanceReport,
    SessionMaintenanceWorker,
)

class FakeMaintainer:
    def __init__(self):
        self.calls = 0

    def run_once(self):
        self.calls += 1
        return SessionIndexMaintenanceReport(
            subject_indexes_scanned=1,
            family_indexes_scanned=1,
            orphan_members_removed=1,
            ttl_repairs=1,
            errors=0,
        )

def test_worker_run_once():
    maintainer = FakeMaintainer()
    worker = SessionMaintenanceWorker(
        maintainer=maintainer,
        interval_seconds=10,
    )

    report = asyncio.run(
        worker.run_once()
    )

    assert maintainer.calls == 1
    assert report.orphan_members_removed == 1
    assert worker.last_report == report
