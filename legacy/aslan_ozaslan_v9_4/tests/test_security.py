import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.security import CsrfManager, LoginAttemptGuard, SessionManager

class SecurityTests(unittest.TestCase):
    def test_session_create_validate_revoke(self):
        manager = SessionManager(ttl_minutes=5)
        token = manager.create("u1", "OWNER")
        self.assertIsNotNone(manager.validate(token))
        manager.revoke(token)
        self.assertIsNone(manager.validate(token))

    def test_csrf_is_bound_to_session(self):
        manager = CsrfManager(secret=b"x"*32)
        token = manager.issue("session-a")
        self.assertTrue(manager.validate("session-a", token))
        self.assertFalse(manager.validate("session-b", token))

    def test_login_lockout(self):
        guard = LoginAttemptGuard(max_failures=2, lock_minutes=10)
        guard.record_failure("ip:1")
        self.assertFalse(guard.is_locked("ip:1"))
        guard.record_failure("ip:1")
        self.assertTrue(guard.is_locked("ip:1"))

if __name__ == "__main__":
    unittest.main()
