import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import IncidentSeverity, IncidentManager

class IncidentTests(unittest.TestCase):
    def test_incident_lifecycle(self):
        manager = IncidentManager()
        incident = manager.create(
            incident_id="inc-1",
            title="Provider outage",
            severity=IncidentSeverity.SEV1,
            owner="ops",
        )
        mitigated = manager.transition(incident, "MITIGATED")
        resolved = manager.transition(mitigated, "RESOLVED")
        self.assertEqual(resolved.status, "RESOLVED")

    def test_resolved_incident_cannot_reopen(self):
        manager = IncidentManager()
        incident = manager.create(
            incident_id="inc-2",
            title="Cache issue",
            severity=IncidentSeverity.SEV2,
        )
        resolved = manager.transition(incident, "RESOLVED")
        with self.assertRaises(ValueError):
            manager.transition(resolved, "OPEN")

if __name__ == "__main__":
    unittest.main()
