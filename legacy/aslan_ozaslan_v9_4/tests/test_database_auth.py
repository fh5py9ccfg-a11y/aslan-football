import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.auth import Permission, RoleAuthorizer, UserRepository
from aslan_ozaslan.database import ProductionDatabase

class DatabaseAuthTests(unittest.TestCase):
    def test_schema_is_created(self):
        with tempfile.TemporaryDirectory() as directory:
            db = ProductionDatabase(Path(directory) / "app.db")
            self.assertEqual(db.schema_version(), 1)

    def test_user_create_and_authenticate(self):
        with tempfile.TemporaryDirectory() as directory:
            db = ProductionDatabase(Path(directory) / "app.db")
            users = UserRepository(db)
            created = users.create(
                email="Owner@Example.com",
                password="StrongPassword123",
                role="OWNER",
            )
            authenticated = users.authenticate(
                "owner@example.com",
                "StrongPassword123",
            )
            self.assertEqual(created.user_id, authenticated.user_id)

    def test_wrong_password_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            db = ProductionDatabase(Path(directory) / "app.db")
            users = UserRepository(db)
            users.create(
                email="analyst@example.com",
                password="StrongPassword123",
                role="ANALYST",
            )
            self.assertIsNone(
                users.authenticate("analyst@example.com", "WrongPassword123")
            )

    def test_viewer_cannot_deploy_model(self):
        auth = RoleAuthorizer()
        self.assertFalse(auth.is_allowed("VIEWER", Permission.DEPLOY_MODEL))
        with self.assertRaises(PermissionError):
            auth.require("VIEWER", Permission.DEPLOY_MODEL)

if __name__ == "__main__":
    unittest.main()
