import sqlite3
import unittest
from datetime import datetime, timedelta, timezone

from app import Handler


class OpeningLooseTests(unittest.TestCase):
    def test_opening_accepts_cartons_and_loose_units(self):
        con = sqlite3.connect(":memory:")
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE items(id INTEGER PRIMARY KEY,group_name TEXT,active INTEGER,units_per_carton INTEGER)")
        con.execute("""CREATE TABLE daily_stock_counts(day TEXT,phase TEXT,item_id INTEGER,quantity TEXT,
            cartons TEXT,loose_units TEXT,created_at TEXT,created_by INTEGER,PRIMARY KEY(day,phase,item_id))""")
        con.execute("""CREATE TABLE audit_log(actor_id INTEGER,action TEXT,entity TEXT,
            entity_id INTEGER,detail TEXT,created_at TEXT)""")
        con.execute("INSERT INTO items VALUES(1,'beer',1,24)")
        day = datetime.now(timezone(timedelta(hours=7))).date().isoformat()
        handler = type("FakeHandler", (), {"require": lambda *args: None})()
        result = Handler.mutate(handler, con, {"id": 1}, "/api/daily-stock-batch",
                                {"day": day, "phase": "opening",
                                 "items": [{"item_id": 1, "cartons": 1, "loose_units": 3}]})
        row = con.execute("SELECT quantity,cartons,loose_units FROM daily_stock_counts").fetchone()
        self.assertEqual(result["count"], 1)
        self.assertEqual(tuple(row), ("27", "1", "3"))
        con.close()


if __name__ == "__main__":
    unittest.main()
