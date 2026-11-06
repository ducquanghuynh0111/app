import tempfile
import unittest
from pathlib import Path

import app
import cukcuk_sync


class ItemTableUsageTest(unittest.TestCase):
    def test_invoice_sync_preserves_table_name(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    cukcuk_sync.store_invoices(con, [{
                        "RefId": "invoice-1", "RefNo": "1", "RefDate": "2025-10-08T20:00:00+07:00",
                        "BranchId": "branch", "TableName": "Bàn 2", "PaymentStatus": 3,
                        "SAInvoiceDetails": [{"RefDetailId": "detail-1", "RefDetailType": 1,
                                              "ItemCode": "BEER", "ItemName": "Bia", "Quantity": 2}],
                    }], "branch")
                    table_name = con.execute("SELECT table_name FROM cukcuk_invoices").fetchone()[0]
                self.assertEqual(table_name, "Bàn 2")
        finally:
            app.DB = original_db

    def test_paid_quantity_is_grouped_by_item_and_table_without_inventing_returns(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("INSERT INTO items(code,name,group_name,unit) VALUES(?,?,?,?)",
                                ("BEER", "Bia", "beer", "lon"))
                    con.execute("INSERT INTO cukcuk_sync_runs(from_date,to_date,completed_at,invoice_count) VALUES(?,?,?,?)",
                                ("2025-10-08", "2025-10-09", "2025-10-10T00:00:00Z", 2))
                    for ref_id, date, table_name, amount in (
                        ("invoice-2", "2025-10-08T20:00:00+07:00", "Bàn 2", "2"),
                        ("invoice-4", "2025-10-09T01:00:00+07:00", "Bàn 4", "3"),
                    ):
                        con.execute("""INSERT INTO cukcuk_invoices
                            (ref_id,ref_no,ref_date,branch_id,payment_status,table_name,total_amount,cash_amount,card_amount,modified_date)
                            VALUES(?,?,?,?,?,?,?,?,?,?)""",
                            (ref_id, ref_id, date, "branch", 3, table_name, "0", "0", "0", date))
                        con.execute("""INSERT INTO cukcuk_invoice_items
                            (detail_id,ref_id,item_code,item_name,quantity,amount) VALUES(?,?,?,?,?,?)""",
                            ("detail-" + ref_id, ref_id, "BEER", "Bia", amount, "0"))
                    report = app.item_table_usage(con, "2025-10-08")
                self.assertTrue(report["synced"])
                self.assertEqual(report["items"][0]["billed_quantity"], "5")
                self.assertEqual({r["table"]: r["billed_quantity"] for r in report["items"][0]["tables"]},
                                 {"Bàn 2": "2", "Bàn 4": "3"})
                self.assertIsNone(report["items"][0]["returned_quantity"])
                self.assertIsNone(report["items"][0]["ordered_quantity"])
        finally:
            app.DB = original_db


if __name__ == "__main__":
    unittest.main()
