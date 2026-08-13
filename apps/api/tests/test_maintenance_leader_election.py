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
            orphan_members_removed=2,
            ttl_repairs=1,
            errors=0,
            duration_ms=3.5,
            lease_acquired=True,
        )

class FakeLease:
    def __init__(self, acquired):
        self.acquired = acquired
        self.releases = 0

    def acquire(self):
        return self.acquired

    def release(self):
        self.releases += 1
        return True

class FakeMetrics:
    def __init__(self):
        self.items = {}

    def increment(self, name, value=1.0):
        self.items[name] = (
            self.items.get(name, 0)
            + value
        )

def test_non_leader_skips_maintenance():
    maintainer = FakeMaintainer()
    metrics = FakeMetrics()
    worker = SessionMaintenanceWorker(
        maintainer=maintainer,
        lease=FakeLease(False),
        metrics=metrics,
        interval_seconds=10,
    )

    report = asyncio.run(worker.run_once())

    assert report.lease_acquired is False
    assert maintainer.calls == 0
    assert (
        metrics.items[
            "aslan_session_maintenance_skipped_total"
        ]
        == 1
    )

def test_leader_runs_and_releases():
    maintainer = FakeMaintainer()
    lease = FakeLease(True)
    metrics = FakeMetrics()
    worker = SessionMaintenanceWorker(
        maintainer=maintainer,
        lease=lease,
        metrics=metrics,
        interval_seconds=10,
    )

    report = asyncio.run(worker.run_once())

    assert report.lease_acquired is True
    assert maintainer.calls == 1
    assert lease.releases == 1
    assert (
        metrics.items[
            "aslan_session_maintenance_runs_total"
        ]
        == 1
    )
    assert (
        metrics.items[
            "aslan_session_maintenance_orphans_removed_total"
        ]
        == 2
    )
