import http.cookiejar
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer

import app


class RestaurantApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        app.DB = Path(self.tmp.name) / "test.db"
        app.init_db()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:%d" % self.server.server_port
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf = ""
        self.request("/api/setup", {"name": "Chủ thử nghiệm", "password": "test-password-12345"}, 201)
        self.request("/api/login", {"username": "owner", "password": "test-password-12345"})
        self.csrf = self.request("/api/me")["csrf"]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def request(self, path, payload=None, expected=200):
        headers = {}
        if payload is not None:
            headers["Content-Type"] = "application/json"
            if self.csrf:
                headers["X-CSRF-Token"] = self.csrf
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers=headers,
            method="POST" if payload is not None else "GET",
        )
        try:
            response = self.opener.open(req)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            data = json.load(response)
            self.assertEqual(response.status, expected, data)
            return data

    def test_cash_reconciliation_and_locked_shift(self):
        sid = self.request("/api/cash-shifts", {"label": "Ca tối", "opening_cash": 50000}, 201)["id"]
        self.request("/api/cash-entries", {
            "shift_id": sid, "kind": "expense", "method": "cash",
            "amount": 10000, "note": "Mua đá", "reference": "P001",
        }, 201)
        summary = self.request("/api/cash-shifts/%d/update" % sid, {
            "manual_cash": 100000, "manual_bank": 20000,
            "counted_cash": 140000, "counted_bank": 20000,
        }, 201)
        self.assertEqual(summary["expected_cash"], 140000)
        self.assertEqual(summary["difference_cash"], 0)
        self.request("/api/cash-shifts/%d/close" % sid, {"reason": ""}, 201)
        self.request("/api/cash-shifts/%d/update" % sid, {
            "manual_cash": 0, "manual_bank": 0, "counted_cash": 0, "counted_bank": 0,
        }, 400)

    def test_frontend_assets_are_served(self):
        for path, expected_type in (("/", "text/html"), ("/app.js", "text/javascript"),
                                    ("/style.css", "text/css")):
            with self.opener.open(self.base + path) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(expected_type, response.headers["Content-Type"])
                self.assertGreater(len(response.read()), 0)

    def test_inventory_count_requires_approval(self):
        item = self.request("/api/items", {
            "code": "BIA-1", "name": "Bia lon", "group_name": "beer",
            "unit": "lon", "min_stock": "5",
        }, 201)["id"]
        self.request("/api/stock-moves", {
            "item_id": item, "kind": "receipt", "quantity": "10",
            "reason": "Nhập đầu ngày",
        }, 201)
        count = self.request("/api/stock-counts", {
            "item_id": item, "counted_qty": "7", "note": "Đếm cuối ca",
        }, 201)
        self.assertEqual(count["difference"], "-3")
        before = self.request("/api/dashboard")["items"][0]
        self.assertEqual(before["balance"], "10")
        self.request("/api/stock-counts/%d/approve" % count["id"], {"reason": "Thiếu cần xác minh"}, 201)
        after = self.request("/api/dashboard")["items"][0]
        self.assertEqual(after["balance"], "7")
        self.request("/api/stock-counts/%d/approve" % count["id"], {"reason": "Lặp"}, 400)

    def test_import_is_idempotent_and_reduces_direct_stock(self):
        item = self.request("/api/items", {
            "code": "BIA-2", "name": "Bia chai", "group_name": "beer",
            "unit": "chai", "min_stock": "0",
        }, 201)["id"]
        self.request("/api/stock-moves", {
            "item_id": item, "kind": "receipt", "quantity": "10", "reason": "Nhập",
        }, 201)
        sid = self.request("/api/cash-shifts", {"label": "Ca 1", "opening_cash": 0}, 201)["id"]
        rows = [{"source_row_id": "BILL-1-L1", "item_code": "BIA-2",
                 "quantity": "2", "amount": 50000, "method": "cash"}]
        self.assertEqual(self.request("/api/sales-import", {"shift_id": sid, "rows": rows}, 201)["inserted"], 1)
        self.assertEqual(self.request("/api/sales-import", {"shift_id": sid, "rows": rows}, 201)["skipped"], 1)
        dashboard = self.request("/api/dashboard")
        self.assertEqual(dashboard["items"][0]["balance"], "8")
        self.assertEqual(dashboard["cash_shifts"][0]["expected_cash"], 50000)
        other = self.request("/api/cash-shifts", {"label": "Ca 2", "opening_cash": 0}, 201)["id"]
        self.request("/api/sales-import", {"shift_id": other, "rows": rows}, 400)

    def test_employee_permissions_and_attendance_order(self):
        employee = self.request("/api/users", {
            "username": "nv01", "name": "Nhân viên 1", "role": "staff",
            "password": "test-password-67890",
        }, 201)["id"]
        work = self.request("/api/work-shifts", {
            "user_id": employee, "starts_at": "2026-11-04T18:00:00",
            "ends_at": "2026-11-04T23:00:00",
        }, 201)["id"]
        self.request("/api/work-shifts/%d/check-in" % work, {}, 403)
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self.csrf = ""
        self.request("/api/login", {"username": "nv01", "password": "test-password-67890"})
        self.csrf = self.request("/api/me")["csrf"]
        dashboard = self.request("/api/dashboard")
        self.assertEqual(len(dashboard["work_shifts"]), 1)
        self.assertNotIn("cash_shifts", dashboard)
        self.request("/api/items", {
            "code": "X", "name": "Không được thêm", "group_name": "beer",
            "unit": "lon", "min_stock": 0,
        }, 403)
        self.request("/api/work-shifts/%d/check-out" % work, {}, 400)
        self.request("/api/work-shifts/%d/check-in" % work, {}, 201)
        self.request("/api/work-shifts/%d/check-out" % work, {}, 201)
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self.csrf = ""
        self.request("/api/login", {"username": "owner", "password": "test-password-12345"})
        self.csrf = self.request("/api/me")["csrf"]
        metrics = self.request("/api/dashboard")["staff_metrics"]
        employee_metrics = next(m for m in metrics if m["name"] == "Nhân viên 1")
        self.assertEqual(employee_metrics["attended"], 1)

    def test_cashier_cannot_change_another_cash_shift(self):
        sid = self.request("/api/cash-shifts", {
            "label": "Ca của chủ", "opening_cash": 0,
        }, 201)["id"]
        self.request("/api/users", {
            "username": "tn01", "name": "Thu ngân 1", "role": "cashier",
            "password": "test-password-67890",
        }, 201)
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self.csrf = ""
        self.request("/api/login", {"username": "tn01", "password": "test-password-67890"})
        self.csrf = self.request("/api/me")["csrf"]
        self.assertEqual(self.request("/api/dashboard")["cash_shifts"], [])
        self.request("/api/cash-shifts/%d/update" % sid, {
            "manual_cash": 0, "manual_bank": 0, "counted_cash": 0, "counted_bank": 0,
        }, 403)


if __name__ == "__main__":
    unittest.main()
