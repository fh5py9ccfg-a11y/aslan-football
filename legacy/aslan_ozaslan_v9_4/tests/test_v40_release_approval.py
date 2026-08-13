import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import ReleaseApprovalWorkflow

class ReleaseApprovalTests(unittest.TestCase):
    def test_two_distinct_approvers_required(self):
        workflow = ReleaseApprovalWorkflow(minimum_approvals=2)
        workflow.approve(release_version="4.0", approver_id="alice")
        self.assertFalse(workflow.is_approved("4.0"))
        workflow.approve(release_version="4.0", approver_id="bob")
        self.assertTrue(workflow.is_approved("4.0"))

    def test_duplicate_approver_does_not_count_twice(self):
        workflow = ReleaseApprovalWorkflow(minimum_approvals=2)
        workflow.approve(release_version="4.0", approver_id="alice")
        workflow.approve(release_version="4.0", approver_id="alice")
        self.assertFalse(workflow.is_approved("4.0"))

if __name__ == "__main__":
    unittest.main()
