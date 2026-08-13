import asyncio

from apps.api.app.session_maintenance import (
    SessionIndexMaintenanceReport,
    SessionMaintenanceWorker,
)

class Maintainer:
    checkpoint = None

    def run_once(self):
        return SessionIndexMaintenanceReport(
            subject_indexes_scanned=1,
            family_indexes_scanned=1,
            orphan_members_removed=0,
            ttl_repairs=0,
            errors=0,
            duration_ms=1,
            lease_acquired=True,
            lease_lost=True,
            aborted=True,
        )

class Lease:
    def acquire(self):
        return True

    def renew(self):
        return True

    def release(self):
        return True

class Metrics:
    def __init__(self):
        self.values = {}

    def increment(self, name, value=1):
        self.values[name] = self.values.get(name, 0) + value

def test_lease_loss_and_abort_metrics():
    metrics = Metrics()
    worker = SessionMaintenanceWorker(
        maintainer=Maintainer(),
        lease=Lease(),
        metrics=metrics,
        interval_seconds=10,
    )

    asyncio.run(worker.run_once())

    assert (
        metrics.values[
            "aslan_session_maintenance_lease_lost_total"
        ]
        == 1
    )
    assert (
        metrics.values[
            "aslan_session_maintenance_aborted_total"
        ]
        == 1
    )
