import tempfile
import unittest
from pathlib import Path

import app
from cukcuk_sync import store_invoices
from saleable_history import history_report, period_bounds


class SaleableHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_db = app.DB
        app.DB = Path(self.tmp.name) / "history.db"
        app.init_db()

    def tearDown(self):
        app.DB = self.original_db
        self.tmp.cleanup()

    def test_day_week_month_bounds(self):
        self.assertEqual(tuple(str(x) for x in period_bounds("day", "2026-01-02")),
                         ("2026-01-02", "2026-01-02"))
        self.assertEqual(tuple(str(x) for x in period_bounds("week", "2026-01-02")),
                         ("2025-12-29", "2026-01-04"))
        self.assertEqual(tuple(str(x) for x in period_bounds("month", "2026-02-15")),
                         ("2026-02-01", "2026-02-28"))
        with self.assertRaises(ValueError):
            period_bounds("year", "2026-01-02")

    def test_converted_business_day_history_and_missing_unit(self):
        with app.db() as con:
            con.execute("INSERT INTO users(id,username,display_name,role,password_hash) VALUES(1,'owner','Owner','owner','x')")
            products = [("BT", "Tiger", "beer", "Lon", 24, "48", "24", "48"),
                        ("NS", "Nước suối", "water", "Chai", 24, "24", "0", "22"),
                        ("TNN", "Thuốc con ngựa", "tobacco", "Gói", 10, "20", "0", "10")]
            for index, (code, name, group, unit, size, previous, incoming, ending) in enumerate(products, 1):
                con.execute("INSERT INTO items(id,code,name,group_name,unit,units_per_carton) VALUES(?,?,?,?,?,?)",
                            (index, code, name, group, unit, size))
                for day, phase, amount in (("2026-01-01", "closing", previous),
                                           ("2026-01-02", "opening", incoming),
                                           ("2026-01-02", "closing", ending)):
                    con.execute("""INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by)
                        VALUES(?,?,?,?,?,1)""", (day, phase, index, amount, day))
            con.execute("""INSERT INTO cukcuk_sync_runs(from_date,to_date,completed_at,invoice_count)
                VALUES('2026-01-02','2026-01-03','2026-01-04',1)""")
            invoice = {"RefId":"bill-1","RefNo":"1","RefDate":"2026-01-03T01:00:00+07:00",
                       "BranchId":"branch","PaymentStatus":3,"TotalAmount":0,
                       "SAInvoiceDetails":[
                           {"RefDetailId":"line-1","RefDetailType":1,"ItemCode":"BT","ItemName":"Tiger",
                            "UnitName":"Thùng","Quantity":1,"Amount":0},
                           {"RefDetailId":"line-2","RefDetailType":1,"ItemCode":"NS","ItemName":"Nước suối",
                            "UnitName":"Chai","Quantity":2,"Amount":0},
                           {"RefDetailId":"line-3","RefDetailType":1,"ItemCode":"TNN","ItemName":"Thuốc con ngựa",
                            "UnitName":"Cây","Quantity":1,"Amount":0}],"SAInvoicePayments":[]}
            store_invoices(con, [invoice], "branch")
            result = history_report(con, "day", "2026-01-02", app.daily_stock_report)
            self.assertEqual(result["days"][0]["status"], "ok")
            rows = {row["code"]:row for row in result["days"][0]["rows"]}
            self.assertEqual((rows["BT"]["sold"],rows["NS"]["sold"],rows["TNN"]["sold"]),
                             ("24", "2", "10"))
            self.assertTrue(all(row["variance"] == "0" for row in rows.values()))
            con.execute("UPDATE cukcuk_invoice_items SET unit_name='' WHERE item_code='BT'")
            missing = history_report(con, "day", "2026-01-02", app.daily_stock_report)["days"][0]
            self.assertEqual(missing["status"], "unit_unknown")
            self.assertIsNone(next(row for row in missing["rows"] if row["code"] == "BT")["variance"])
            con.execute("DELETE FROM cukcuk_sync_runs")
            unsynced = history_report(con, "day", "2026-01-02", app.daily_stock_report)["days"][0]
            self.assertEqual(unsynced["status"], "unsynced")
            self.assertTrue(all(row["sold"] is None for row in unsynced["rows"]))


if __name__ == "__main__":
    unittest.main()
