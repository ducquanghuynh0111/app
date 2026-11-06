import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import app
from cukcuk_sync import Client, store_invoices


class CukcukSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = app.DB
        app.DB = Path(self.tmp.name) / "test.db"
        app.init_db()

    def tearDown(self):
        app.DB = self.old_db
        self.tmp.cleanup()

    def test_signed_login_and_paging(self):
        calls = []
        def fake(path, body, headers=None):
            calls.append((path, body, headers))
            if path.endswith("Login"):
                self.assertEqual(list(body), ["AppID", "Domain", "LoginTime", "SignatureInfo"])
                self.assertEqual(len(body["SignatureInfo"]), 64)
                return {"Data": {"AccessToken": "fake", "CompanyCode": "test"}}
            self.assertEqual(body["Limit"], 100)
            self.assertEqual(headers["CompanyCode"], "test")
            return {"Data": [{"RefId": str(body["Page"])}], "Total": 101} if body["Page"] == 1 else {"Data": [{"RefId": "2"}], "Total": 101}
        client = Client("app", "domain", "secret", "branch", fake)
        self.assertEqual(len(list(client.invoices(date(2026, 1, 1), date(2026, 1, 31)))), 2)
        self.assertEqual([call[1]["Page"] for call in calls[1:]], [1, 2])

    def test_branch_list_uses_get(self):
        paths = []

        def post(path, body, headers=None):
            paths.append(("POST", path))
            return {"Data": {"AccessToken": "fake", "CompanyCode": "test"}}

        def get(path, headers):
            paths.append(("GET", path))
            return {"Data": [{"Id": "branch", "Inactive": False}]}

        client = Client("app", "domain", "secret", "", post, get)
        client.login()
        client.resolve_branch()
        self.assertEqual(client.branch_id, "branch")
        self.assertEqual(paths[-1], ("GET", "/api/v1/branchs/all"))

    def test_order_paging_and_detail_use_read_only_endpoints(self):
        order_id = "11111111-1111-1111-1111-111111111111"
        paths = []
        def post(path, body, headers=None):
            paths.append(path)
            if path.endswith("Login"):
                return {"Data": {"AccessToken": "fake", "CompanyCode": "company"}}
            self.assertEqual(body["BranchId"], "branch")
            self.assertEqual(body["Limit"], 100)
            return {"Data": [{"Id": order_id, "Status": 1}], "Total": 1}
        def get(path, headers):
            paths.append(path)
            self.assertEqual(headers["Authorization"], "Bearer fake")
            return {"Data": {"Id": order_id, "OrderDetails": []}}
        client = Client("app", "domain", "secret", "branch", post, get)
        self.assertEqual(len(list(client.orders_since(datetime(2026, 11, 4, tzinfo=timezone.utc)))), 1)
        self.assertEqual(client.order_detail(order_id)["Id"], order_id)
        self.assertEqual(paths, ["/api/Account/Login", "/api/v1/orders/paging", "/api/v1/orders/" + order_id])

    def test_invoice_import_is_idempotent_and_daily_variance(self):
        invoice = {"RefId": "bill-1", "RefNo": "1", "RefDate": "2026-01-02T18:00:00+07:00",
                   "BranchId": "branch", "PaymentStatus": 3, "TotalAmount": 50000,
                   "CashAmount": 50000, "CardAmount": 0,
                   "SAInvoiceDetails": [{"RefDetailId": "line-1", "RefDetailType": 1,
                                           "ItemCode": "BIA", "ItemName": "Bia", "Quantity": 2,
                                           "UnitName": "Lon", "Amount": 50000}],
                   "SAInvoicePayments": [{"SAInvoicePaymentID": "payment-1", "PaymentType": 1, "Amount": 50000}]}
        with app.db() as con:
            con.execute("INSERT INTO users(username,display_name,role,password_hash) VALUES('owner','Owner','owner','x')")
            con.execute("INSERT INTO items(code,name,group_name,unit) VALUES('BIA','Bia','beer','lon')")
            con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES('2026-01-01','closing',1,'20','2026-01-01',1)")
            con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES('2026-01-02','opening',1,'0','2026-01-02',1)")
            con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES('2026-01-02','closing',1,'18','2026-01-02',1)")
            con.execute("INSERT INTO cukcuk_sync_runs(from_date,to_date,completed_at,invoice_count) VALUES('2026-01-02','2026-01-03','2026-01-04',1)")
            store_invoices(con, [invoice], "branch")
            store_invoices(con, [invoice], "branch")
            self.assertEqual(con.execute("SELECT COUNT(*) FROM cukcuk_invoice_items").fetchone()[0], 1)
            self.assertEqual(app.cukcuk_summary(con, "2026-01-02", "2026-01-02")["beer_tobacco"][0]["quantity"], "2")
            row = app.daily_stock_report(con, "2026-01-02")[0]
            self.assertEqual((row["expected"], row["variance"]), ("18", "0"))
            con.execute("INSERT INTO items(code,name,group_name,unit) VALUES('MEAT','Meat','ingredient','kg')")
            con.execute("INSERT INTO recipes VALUES('MON',2,'0.2')")
            con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES('2026-01-02','opening',2,'10','2026-01-02',1)")
            invoice["SAInvoiceDetails"].append({"RefDetailId": "line-2", "RefDetailType": 1,
                                                 "ItemCode": "MON", "ItemName": "Món", "Quantity": 3, "Amount": 0})
            store_invoices(con, [invoice], "branch")
            meat = next(row for row in app.daily_stock_report(con, "2026-01-02") if row["code"] == "MEAT")
            self.assertEqual((meat["recipe_used"], meat["expected"]), ("0.6", "9.4"))

    def test_kiosk_punch_uses_scheduled_shift_once(self):
        start = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        end = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        with app.db() as con:
            con.execute("INSERT INTO users(username,display_name,role,password_hash) VALUES('nv1','NV 1','staff','x')")
            con.execute("INSERT INTO kiosk_pins VALUES(1,?)", (app.password_hash("123456"),))
            con.execute("INSERT INTO work_shifts(user_id,starts_at,ends_at) VALUES(1,?,?)", (start, end))
            self.assertEqual(app.kiosk_punch(con, "nv1", "123456", "check-in")["shift_id"], 1)
            self.assertEqual(app.kiosk_punch(con, "nv1", "123456", "check-out")["shift_id"], 1)
            row = con.execute("SELECT checked_in_at,checked_out_at FROM work_shifts WHERE id=1").fetchone()
            self.assertTrue(row["checked_in_at"] and row["checked_out_at"])


if __name__ == "__main__":
    unittest.main()
