import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import RunbookHistory
from aslan_ozaslan.admin import render_runbook_history_page

class RunbookPageTests(unittest.TestCase):
    def test_page_renders_execution(self):
        history = RunbookHistory()
        execution = history.start("exec-1", "provider_down", "ops")
        execution = history.record_step("exec-1", "confirm-impact")
        page = render_runbook_history_page([execution])
        self.assertIn("Runbook Yürütme Geçmişi", page)
        self.assertIn("confirm-impact", page)

if __name__ == "__main__":
    unittest.main()
