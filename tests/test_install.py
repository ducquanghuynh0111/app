import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import caidat
from import_database import import_database


class InstallTest(unittest.TestCase):
    def test_creates_empty_database_and_preserves_it_on_second_run(self):
        with tempfile.TemporaryDirectory(dir=caidat.ROOT) as temporary:
            database = Path(temporary) / "data" / "restaurant.db"
            with patch.object(caidat, "DATABASE", database):
                self.assertTrue(caidat.install())
                with closing(sqlite3.connect(database)) as connection:
                    tables = [row[0] for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )]
                    self.assertGreaterEqual(len(tables), 30)
                    for table in tables:
                        count = connection.execute(
                            'SELECT count(*) FROM "' + table.replace('"', '""') + '"'
                        ).fetchone()[0]
                        self.assertEqual(count, 0, table)
                    self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertFalse(caidat.install())

    def test_import_rejects_data_commands(self):
        with tempfile.TemporaryDirectory(dir=caidat.ROOT) as temporary:
            source = Path(temporary) / "bad.sql"
            target = Path(temporary) / "bad.db"
            source.write_text("CREATE TABLE x(id INTEGER);\nINSERT INTO x VALUES(1);\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                import_database(source, target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
