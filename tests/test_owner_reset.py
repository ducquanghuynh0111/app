import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app
import reset_owner_password


class OwnerResetTest(unittest.TestCase):
    def test_reset_changes_owner_password_and_revokes_sessions(self):
        previous_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("""INSERT INTO users
                        (username,display_name,role,department,password_hash)
                        VALUES(?,?,?,?,?)""",
                        ("owner", "Owner", "owner", "management", app.password_hash("PreviousPass123")))
                    con.execute("INSERT INTO sessions(token_hash,user_id,csrf,expires_at) VALUES(?,?,?,?)",
                                ("test-session", 1, "test-csrf", "2099-01-01T00:00:00Z"))
                with mock.patch("sys.stdin.isatty", return_value=True), \
                     mock.patch("getpass.getpass", side_effect=["ReplacementPass123", "ReplacementPass123"]), \
                     mock.patch("builtins.print"):
                    self.assertEqual(reset_owner_password.main(), 0)
                with app.db() as con:
                    hashed = con.execute("SELECT password_hash FROM users WHERE username='owner'").fetchone()[0]
                    self.assertTrue(app.password_valid("ReplacementPass123", hashed))
                    self.assertFalse(app.password_valid("PreviousPass123", hashed))
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], 0)
        finally:
            app.DB = previous_db


if __name__ == "__main__":
    unittest.main()
