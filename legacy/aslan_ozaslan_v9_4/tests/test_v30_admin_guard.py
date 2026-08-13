import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.admin import AdminRequestContext, AdminRouteGuard
from aslan_ozaslan.security import SessionManager, CsrfManager

class AdminGuardTests(unittest.TestCase):
    def test_admin_write_requires_csrf(self):
        sessions = SessionManager()
        csrf = CsrfManager(secret=b"x" * 32)
        token = sessions.create("u1", "ADMIN")
        guard = AdminRouteGuard(sessions, csrf)
        with self.assertRaises(PermissionError):
            guard.authorize(AdminRequestContext(token, None, "POST"))
        valid_csrf = csrf.issue(token)
        session = guard.authorize(AdminRequestContext(token, valid_csrf, "POST"))
        self.assertEqual(session.role, "ADMIN")

if __name__ == "__main__":
    unittest.main()
