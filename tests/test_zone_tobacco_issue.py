import sqlite3
import unittest

from app import ApiError, Handler
from zone_shift_report import business_day, init_db
from app import now


class ZoneTobaccoIssueTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row
        self.con.execute("CREATE TABLE zones(id INTEGER PRIMARY KEY, active INTEGER NOT NULL)")
        self.con.execute("CREATE TABLE users(id INTEGER PRIMARY KEY)")
        self.con.execute("""CREATE TABLE audit_log(actor_id INTEGER,action TEXT,entity TEXT,
            entity_id INTEGER,detail TEXT,created_at TEXT)""")
        self.con.execute("INSERT INTO zones VALUES(1,1)")
        self.con.execute("INSERT INTO users VALUES(1)")
        init_db(self.con)
        self.handler = type("FakeHandler", (), {"require": lambda *args: None})()
        self.day = business_day(now())

    def tearDown(self):
        self.con.close()

    def mutate(self, path, **data):
        return Handler.mutate(self.handler, self.con, {"id": 1}, path,
                              {"day": self.day, "zone_id": 1, "item_code": "TNN", **data})

    def test_each_press_adds_one_pack_and_preserves_returned_count(self):
        first = self.mutate("/api/zone-tobacco-issue")
        second = self.mutate("/api/zone-tobacco-issue")
        self.assertEqual(first["allocations"][0]["issued"], "1")
        self.assertEqual(second["allocations"][0]["issued"], "2")
        self.assertEqual(second["allocations"][0]["returned"], "0")
        returned = self.mutate("/api/zone-tobacco-allocation", returned=1)
        self.assertEqual(returned["allocations"][0]["issued"], "2")
        self.assertEqual(returned["allocations"][0]["returned"], "1")
        third = self.mutate("/api/zone-tobacco-issue")
        self.assertEqual(third["allocations"][0]["issued"], "3")
        self.assertEqual(third["allocations"][0]["returned"], "1")
        corrected = self.mutate("/api/zone-tobacco-unissue")
        self.assertEqual(corrected["allocations"][0]["issued"], "2")
        self.assertEqual(corrected["allocations"][0]["returned"], "1")
        self.assertEqual(self.con.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action='issue'").fetchone()[0], 3)
        self.assertEqual(self.con.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action='correct-issue'").fetchone()[0], 1)

    def test_correction_cannot_go_below_zero(self):
        with self.assertRaises(ApiError):
            self.mutate("/api/zone-tobacco-unissue")


if __name__ == "__main__":
    unittest.main()
