import tempfile
import unittest
import json
import copy
import os
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path

import app
from order_monitor import create_late_events, save_order, poll_once


class OrderMonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = app.DB
        app.DB = Path(self.tmp.name) / "test.db"
        app.init_db()
        self.base = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)
        self.order = {"Id": "order-a", "No": "12.3", "TableName": "12", "Status": 1,
                      "OrderDetails": [{"Id": "line-a", "ItemName": "Bò nướng", "Quantity": 2},
                                       {"Id": "extra", "ItemName": "Không cay", "Quantity": 1,
                                        "ParentId": "line-a"}]}

    def tearDown(self):
        app.DB = self.old_db
        self.tmp.cleanup()

    def test_new_late_repeat_and_served(self):
        with app.db() as con:
            self.assertEqual(save_order(con, self.order, self.base.isoformat()), 1)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM runner_items").fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT kind FROM runner_events").fetchone()[0], "new")
            self.assertEqual(create_late_events(con, self.base+timedelta(minutes=14), 15, 5), 0)
            self.assertEqual(create_late_events(con, self.base+timedelta(minutes=15), 15, 5), 1)
            self.assertEqual(create_late_events(con, self.base+timedelta(minutes=19), 15, 5), 0)
            self.assertEqual(create_late_events(con, self.base+timedelta(minutes=20), 15, 5), 1)
            con.execute("UPDATE runner_items SET served_at=?,served_quantity=source_quantity WHERE detail_id='order-a:line-a'", (app.now(),))
            self.assertEqual(create_late_events(con, self.base+timedelta(minutes=30), 15, 5), 0)

    def test_added_and_removed_line(self):
        with app.db() as con:
            save_order(con, self.order, self.base.isoformat(), announce=False)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM runner_events").fetchone()[0], 0)
            self.order["OrderDetails"].append({"Id": "line-b", "ItemName": "Rau", "Quantity": 1})
            self.assertEqual(save_order(con, self.order, (self.base+timedelta(minutes=1)).isoformat()), 1)
            self.assertEqual(con.execute("SELECT kind FROM runner_events").fetchone()[0], "new")
            self.order["OrderDetails"] = []
            save_order(con, self.order, (self.base+timedelta(minutes=2)).isoformat())
            self.assertEqual(con.execute("SELECT COUNT(*) FROM runner_items WHERE canceled_at IS NOT NULL").fetchone()[0], 2)

    def test_added_quantity_reopens_served_line(self):
        with app.db() as con:
            save_order(con, self.order, self.base.isoformat())
            con.execute("UPDATE runner_items SET served_at=?,served_quantity=source_quantity WHERE detail_id='order-a:line-a'", (self.base.isoformat(),))
            self.order["OrderDetails"][0]["Quantity"] = 3
            save_order(con, self.order, (self.base+timedelta(minutes=2)).isoformat())
            row = con.execute("SELECT quantity,served_at,first_seen_at FROM runner_items WHERE detail_id='order-a:line-a'").fetchone()
            self.assertEqual(row["quantity"], "1")
            self.assertIsNone(row["served_at"])
            self.assertEqual(row["first_seen_at"], (self.base+timedelta(minutes=2)).isoformat())

    def test_added_quantity_announces_only_new_parts(self):
        with app.db() as con:
            save_order(con, self.order, self.base.isoformat())
            self.order["OrderDetails"][0]["Quantity"] = 4
            save_order(con, self.order, (self.base+timedelta(minutes=1)).isoformat())
            event = con.execute("SELECT kind,quantity FROM runner_events ORDER BY id DESC LIMIT 1").fetchone()
            self.assertEqual((event["kind"], event["quantity"]), ("added", "2"))

    def test_kds_status_closes_only_after_configured_transition(self):
        old_mode = os.environ.get("RUNNER_COMPLETION_MODE")
        old_statuses = os.environ.get("CUKCUK_KDS_DONE_STATUSES")
        os.environ["RUNNER_COMPLETION_MODE"] = "kds"
        os.environ["CUKCUK_KDS_DONE_STATUSES"] = "99"  # Chỉ là mã giả lập cho bài kiểm tra.
        try:
            self.order["OrderDetails"][0]["Status"] = 1
            with app.db() as con:
                save_order(con, self.order, self.base.isoformat())
                self.assertEqual(create_late_events(con, self.base+timedelta(minutes=15), 15, 5), 1)
                self.order["OrderDetails"][0]["Status"] = 99
                save_order(con, self.order, (self.base+timedelta(minutes=16)).isoformat())
                self.assertEqual(create_late_events(con, self.base+timedelta(minutes=30), 15, 5), 0)
                row = con.execute("SELECT served_at,quantity FROM runner_items WHERE detail_id='order-a:line-a'").fetchone()
                self.assertIsNotNone(row["served_at"])
                self.assertEqual(row["quantity"], "0")
                event = con.execute("SELECT kind,quantity FROM runner_events ORDER BY id DESC LIMIT 1").fetchone()
                self.assertEqual((event["kind"], event["quantity"]), ("ready", "2"))
        finally:
            if old_mode is None: os.environ.pop("RUNNER_COMPLETION_MODE", None)
            else: os.environ["RUNNER_COMPLETION_MODE"] = old_mode
            if old_statuses is None: os.environ.pop("CUKCUK_KDS_DONE_STATUSES", None)
            else: os.environ["CUKCUK_KDS_DONE_STATUSES"] = old_statuses

    def test_poll_announces_total_then_ready_and_remaining_without_table(self):
        old_mode = os.environ.get("RUNNER_COMPLETION_MODE")
        old_statuses = os.environ.get("CUKCUK_KDS_DONE_STATUSES")
        os.environ["RUNNER_COMPLETION_MODE"] = "kds"
        os.environ["CUKCUK_KDS_DONE_STATUSES"] = "99"

        class FakeClient:
            branch_id = "branch"
            orders = {}

            def orders_since(self, _since):
                return [{"Id": key, "Status": order["Status"]} for key, order in self.orders.items()]

            def order_detail(self, order_id):
                return copy.deepcopy(self.orders[order_id])

        client = FakeClient()
        try:
            poll_once(client, 15, 5)  # Establish the initial baseline.
            client.orders["a"] = {"Id": "a", "No": "1", "TableName": "2", "Status": 1,
                "OrderDetails": [{"Id": "a1", "ItemId": "bo", "ItemName": "Bò nướng", "Quantity": 1, "Status": 1}]}
            poll_once(client, 15, 5)
            client.orders["b"] = {"Id": "b", "No": "2", "TableName": "4", "Status": 1,
                "OrderDetails": [{"Id": "b1", "ItemId": "bo", "ItemName": "Bò nướng", "Quantity": 1, "Status": 1}]}
            poll_once(client, 15, 5)
            with app.db() as con:
                rows = con.execute("SELECT kind,quantity FROM runner_events ORDER BY id").fetchall()
                self.assertEqual([(r["kind"], r["quantity"]) for r in rows], [("total", "1"), ("total", "2")])
            client.orders["a"]["OrderDetails"][0]["Status"] = 99
            poll_once(client, 15, 5)
            with app.db() as con:
                event = con.execute("SELECT kind,quantity,table_name,remaining_text FROM runner_events ORDER BY id DESC LIMIT 1").fetchone()
                self.assertEqual((event["kind"], event["quantity"]), ("ready", "1"))
                self.assertIsNone(event["table_name"])
                self.assertEqual(event["remaining_text"], "Còn 1 phần")
            client.orders["b"]["Status"] = 5
            poll_once(client, 15, 5)
            with app.db() as con:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM runner_events").fetchone()[0], 3)
        finally:
            if old_mode is None: os.environ.pop("RUNNER_COMPLETION_MODE", None)
            else: os.environ["RUNNER_COMPLETION_MODE"] = old_mode
            if old_statuses is None: os.environ.pop("CUKCUK_KDS_DONE_STATUSES", None)
            else: os.environ["CUKCUK_KDS_DONE_STATUSES"] = old_statuses

    def test_same_poll_ready_and_new_order_reads_remaining_once(self):
        old_mode = os.environ.get("RUNNER_COMPLETION_MODE")
        old_statuses = os.environ.get("CUKCUK_KDS_DONE_STATUSES")
        os.environ["RUNNER_COMPLETION_MODE"] = "kds"
        os.environ["CUKCUK_KDS_DONE_STATUSES"] = "99"

        class FakeClient:
            branch_id = "branch"
            orders = {}
            def orders_since(self, _since):
                return [{"Id": key, "Status": order["Status"]} for key, order in self.orders.items()]
            def order_detail(self, order_id):
                return copy.deepcopy(self.orders[order_id])

        client = FakeClient()
        try:
            poll_once(client, 15, 5)
            client.orders["a"] = {"Id": "a", "No": "1", "TableName": "2", "Status": 1,
                "OrderDetails": [{"Id": "a1", "ItemId": "bo", "ItemName": "Bò nướng", "Quantity": 1, "Status": 1}]}
            poll_once(client, 15, 5)
            client.orders["a"]["OrderDetails"][0]["Status"] = 99
            client.orders["b"] = {"Id": "b", "No": "2", "TableName": "4", "Status": 1,
                "OrderDetails": [{"Id": "b1", "ItemId": "bo", "ItemName": "Bò nướng", "Quantity": 1, "Status": 1}]}
            poll_once(client, 15, 5)
            with app.db() as con:
                events = con.execute("SELECT kind,remaining_text FROM runner_events ORDER BY id").fetchall()
                self.assertEqual([row["kind"] for row in events], ["total", "ready"])
                self.assertEqual(events[-1]["remaining_text"], "Còn 1 phần")
        finally:
            if old_mode is None: os.environ.pop("RUNNER_COMPLETION_MODE", None)
            else: os.environ["RUNNER_COMPLETION_MODE"] = old_mode
            if old_statuses is None: os.environ.pop("CUKCUK_KDS_DONE_STATUSES", None)
            else: os.environ["CUKCUK_KDS_DONE_STATUSES"] = old_statuses

    def test_two_new_tables_in_one_scan_make_one_total_event(self):
        class FakeClient:
            branch_id = "branch"
            orders = {}
            def orders_since(self, _since):
                return [{"Id": key, "Status": 1} for key in self.orders]
            def order_detail(self, order_id):
                return copy.deepcopy(self.orders[order_id])

        client = FakeClient()
        poll_once(client, 15, 5)
        for order_id, table in (("a", "2"), ("b", "4")):
            client.orders[order_id] = {"Id": order_id, "No": order_id, "TableName": table, "Status": 1,
                "OrderDetails": [{"Id": order_id + "1", "ItemId": "bo", "ItemName": "Bò nướng", "Quantity": 1}]}
        poll_once(client, 15, 5)
        with app.db() as con:
            events = con.execute("SELECT kind,quantity,added_quantity FROM runner_events").fetchall()
            self.assertEqual([(row["kind"], row["quantity"], row["added_quantity"]) for row in events],
                             [("total", "2", "2")])

    def test_new_three_parts_after_two_pending_reports_delta_and_total(self):
        class FakeClient:
            branch_id = "branch"
            orders = {}
            def orders_since(self, _since):
                return [{"Id": key, "Status": 1} for key in self.orders]
            def order_detail(self, order_id):
                return copy.deepcopy(self.orders[order_id])

        client = FakeClient()
        poll_once(client, 15, 5)
        client.orders["a"] = {"Id": "a", "No": "a", "TableName": "2", "Status": 1,
            "OrderDetails": [{"Id": "a1", "ItemId": "mi", "ItemName": "Mì xào", "Quantity": 2}]}
        poll_once(client, 15, 5)
        client.orders["b"] = {"Id": "b", "No": "b", "TableName": "4", "Status": 1,
            "OrderDetails": [{"Id": "b1", "ItemId": "mi", "ItemName": "Mì xào", "Quantity": 3}]}
        poll_once(client, 15, 5)
        with app.db() as con:
            event = con.execute("SELECT kind,quantity,added_quantity FROM runner_events ORDER BY id DESC LIMIT 1").fetchone()
            self.assertEqual((event["kind"], event["quantity"], event["added_quantity"]),
                             ("total", "5", "3"))
        old_key = os.environ.get("RUNNER_DEVICE_KEY")
        os.environ["RUNNER_DEVICE_KEY"] = "c" * 40
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/api/runner/queue?after=0",
                headers={"X-Runner-Key": "c" * 40})
            with urllib.request.urlopen(request) as response:
                events = json.load(response)["events"]
            self.assertEqual(events[-1]["added_quantity"], "3")
            self.assertEqual(events[-1]["quantity"], "5")
        finally:
            server.shutdown(); server.server_close(); worker.join(timeout=2)
            if old_key is None: os.environ.pop("RUNNER_DEVICE_KEY", None)
            else: os.environ["RUNNER_DEVICE_KEY"] = old_key

    def test_two_tables_finish_same_dish_in_one_scan_make_one_ready_event(self):
        old_mode = os.environ.get("RUNNER_COMPLETION_MODE")
        old_statuses = os.environ.get("CUKCUK_KDS_DONE_STATUSES")
        os.environ["RUNNER_COMPLETION_MODE"] = "kds"
        os.environ["CUKCUK_KDS_DONE_STATUSES"] = "99"

        class FakeClient:
            branch_id = "branch"
            orders = {}
            def orders_since(self, _since):
                return [{"Id": key, "Status": 1} for key in self.orders]
            def order_detail(self, order_id):
                return copy.deepcopy(self.orders[order_id])

        client = FakeClient()
        try:
            poll_once(client, 15, 5)
            for order_id, table in (("a", "2"), ("b", "4"), ("c", "6")):
                client.orders[order_id] = {"Id": order_id, "No": order_id, "TableName": table, "Status": 1,
                    "OrderDetails": [{"Id": order_id + "1", "ItemId": "bo", "ItemName": "Bò nướng", "Quantity": 1, "Status": 1}]}
            poll_once(client, 15, 5)
            client.orders["a"]["OrderDetails"][0]["Status"] = 99
            client.orders["b"]["OrderDetails"][0]["Status"] = 99
            poll_once(client, 15, 5)
            with app.db() as con:
                events = con.execute("SELECT kind,quantity,remaining_text FROM runner_events ORDER BY id").fetchall()
                self.assertEqual([(r["kind"], r["quantity"]) for r in events], [("total", "3"), ("ready", "2")])
                self.assertEqual(events[-1]["remaining_text"], "Còn 1 phần")
        finally:
            if old_mode is None: os.environ.pop("RUNNER_COMPLETION_MODE", None)
            else: os.environ["RUNNER_COMPLETION_MODE"] = old_mode
            if old_statuses is None: os.environ.pop("CUKCUK_KDS_DONE_STATUSES", None)
            else: os.environ["CUKCUK_KDS_DONE_STATUSES"] = old_statuses

    def test_runner_api_requires_device_key_and_serves(self):
        old_key = os.environ.get("RUNNER_DEVICE_KEY")
        os.environ["RUNNER_DEVICE_KEY"] = "a" * 40
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with app.db() as con:
                save_order(con, self.order, app.now())
            url = f"http://127.0.0.1:{server.server_port}"
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(url + "/api/runner/queue")
            self.assertEqual(error.exception.code, 403)
            request = urllib.request.Request(url + "/api/runner/queue", headers={"X-Runner-Key": "a" * 40})
            with urllib.request.urlopen(request) as response:
                data = json.load(response)
            self.assertEqual(len(data["items"]), 1)
            request = urllib.request.Request(url + "/api/runner/serve",
                data=json.dumps({"detail_id": "order-a:line-a"}).encode(), method="POST",
                headers={"X-Runner-Key": "a" * 40, "Content-Type": "application/json"})
            with urllib.request.urlopen(request) as response:
                self.assertTrue(json.load(response)["ok"])
            with urllib.request.urlopen(urllib.request.Request(url + "/api/runner/queue",
                    headers={"X-Runner-Key": "a" * 40})) as response:
                self.assertEqual(len(json.load(response)["items"]), 0)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)
            if old_key is None:
                del os.environ["RUNNER_DEVICE_KEY"]
            else:
                os.environ["RUNNER_DEVICE_KEY"] = old_key

    def test_kds_mode_rejects_extra_served_tap(self):
        old_key = os.environ.get("RUNNER_DEVICE_KEY")
        old_mode = os.environ.get("RUNNER_COMPLETION_MODE")
        os.environ["RUNNER_DEVICE_KEY"] = "b" * 40
        os.environ["RUNNER_COMPLETION_MODE"] = "kds"
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with app.db() as con:
                save_order(con, self.order, app.now())
            request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/api/runner/serve",
                data=json.dumps({"detail_id": "order-a:line-a"}).encode(), method="POST",
                headers={"X-Runner-Key": "b" * 40, "Content-Type": "application/json"})
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(request)
            self.assertEqual(error.exception.code, 409)
        finally:
            server.shutdown(); server.server_close(); worker.join(timeout=2)
            if old_key is None: os.environ.pop("RUNNER_DEVICE_KEY", None)
            else: os.environ["RUNNER_DEVICE_KEY"] = old_key
            if old_mode is None: os.environ.pop("RUNNER_COMPLETION_MODE", None)
            else: os.environ["RUNNER_COMPLETION_MODE"] = old_mode


if __name__ == "__main__":
    unittest.main()
