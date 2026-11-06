import tempfile
import unittest
from pathlib import Path

import app


class InventoryGroupsTest(unittest.TestCase):
    def test_unentered_daily_values_remain_unknown_in_report(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("INSERT INTO items(code,name,group_name,unit,units_per_carton) VALUES(?,?,?,?,?)",
                                ("BEER", "Bia", "beer", "lon", 24))
                    day = app.datetime.now(app.timezone(app.timedelta(hours=7))).date().isoformat()
                    row = next(r for r in app.daily_stock_report(con, day) if r["code"] == "BEER")
                    self.assertEqual(row["opening"], "0")
                    self.assertIsNone(row["incoming"])
                    self.assertIsNone(row["closing"])
                    self.assertIsNone(row["variance"])
        finally:
            app.DB = original_db

    def test_closing_count_accepts_loose_units_and_only_manager_can_save(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("PRAGMA foreign_keys=OFF")
                    con.execute("INSERT INTO items(code,name,group_name,unit,units_per_carton) VALUES(?,?,?,?,?)",
                                ("BEER", "Bia", "beer", "lon", 24))
                    handler = app.Handler.__new__(app.Handler)
                    day = app.datetime.now(app.timezone(app.timedelta(hours=7))).date().isoformat()
                    payload = {"day": day, "phase": "closing", "items": [
                        {"item_id": 1, "cartons": "2", "loose_units": "3"}]}
                    with self.assertRaises(app.ApiError):
                        handler.mutate(con, {"id": 2, "role": "stock"}, "/api/daily-stock-batch", payload)
                    handler.mutate(con, {"id": 1, "role": "manager"}, "/api/daily-stock-batch", payload)
                    saved = con.execute("SELECT quantity,cartons,loose_units FROM daily_stock_counts").fetchone()
                    self.assertEqual(tuple(saved), ("51", "2", "3"))
                    with self.assertRaises(app.ApiError):
                        handler.mutate(con, {"id": 1, "role": "manager"}, "/api/daily-stock-batch",
                                       {**payload, "items": [{"item_id": 1, "cartons": "1", "loose_units": "24"}]})
                    self.assertEqual(con.execute("SELECT quantity FROM daily_stock_counts").fetchone()[0], "51")
        finally:
            app.DB = original_db

    def test_bottled_water_invoice_reconciles_daily_count(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("PRAGMA foreign_keys=OFF")
                    con.execute("INSERT INTO items(code,name,group_name,unit) VALUES(?,?,?,?)",
                                ("WATER1", "Nước chai", "water", "chai"))
                    con.execute("INSERT INTO cukcuk_sync_runs(from_date,to_date,completed_at,invoice_count) VALUES(?,?,?,?)",
                                ("2025-10-08", "2025-10-09", "2025-10-10T00:00:00Z", 1))
                    con.execute("""INSERT INTO cukcuk_invoices
                        (ref_id,ref_no,ref_date,branch_id,payment_status,total_amount,cash_amount,card_amount,modified_date)
                        VALUES(?,?,?,?,?,?,?,?,?)""",
                        ("invoice-1", "1", "2025-10-08T12:00:00+07:00", "branch-1", 3,
                         "30000", "30000", "0", "2025-10-08T12:00:00+07:00"))
                    con.execute("""INSERT INTO cukcuk_invoice_items
                        (detail_id,ref_id,item_code,item_name,quantity,amount,unit_name) VALUES(?,?,?,?,?,?,?)""",
                        ("detail-1", "invoice-1", "water1", "Nước chai", "3", "30000", "Chai"))
                    con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES(?,?,?,?,?,?)",
                                ("2025-10-08", "opening", 1, "10", "2025-10-08", 1))
                    con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES(?,?,?,?,?,?)",
                                ("2025-10-07", "closing", 1, "5", "2025-10-07", 1))
                    con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES(?,?,?,?,?,?)",
                                ("2025-10-08", "closing", 1, "12", "2025-10-08", 1))
                    row = app.daily_stock_report(con, "2025-10-08")[0]
                self.assertEqual(row["sold"], "3")
                self.assertEqual(row["expected"], "12")
                self.assertEqual(row["variance"], "0")
        finally:
            app.DB = original_db

    def test_carton_sale_is_converted_and_unknown_unit_does_not_create_false_loss(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("PRAGMA foreign_keys=OFF")
                    con.execute("INSERT INTO items(code,name,group_name,unit,units_per_carton) VALUES(?,?,?,?,?)",
                                ("BT", "Bia Tiger", "beer", "Lon", 24))
                    con.execute("INSERT INTO cukcuk_sync_runs(from_date,to_date,completed_at,invoice_count) VALUES(?,?,?,?)",
                                ("2025-10-08", "2025-10-09", "2025-10-10", 1))
                    con.execute("""INSERT INTO cukcuk_invoices
                        (ref_id,ref_no,ref_date,branch_id,payment_status,total_amount,cash_amount,card_amount,modified_date)
                        VALUES(?,?,?,?,?,?,?,?,?)""",
                        ("invoice-1", "1", "2025-10-08T12:00:00+07:00", "branch-1", 3, "0", "0", "0", ""))
                    con.execute("""INSERT INTO cukcuk_invoice_items
                        (detail_id,ref_id,item_code,item_name,quantity,amount,unit_name) VALUES(?,?,?,?,?,?,?)""",
                        ("detail-1", "invoice-1", "BT", "Bia Tiger", "1", "0", "Thùng"))
                    con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES(?,?,?,?,?,?)",
                                ("2025-10-07", "closing", 1, "48", "2025-10-07", 1))
                    con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES(?,?,?,?,?,?)",
                                ("2025-10-08", "opening", 1, "0", "2025-10-08", 1))
                    con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES(?,?,?,?,?,?)",
                                ("2025-10-08", "closing", 1, "24", "2025-10-08", 1))
                    row = app.daily_stock_report(con, "2025-10-08")[0]
                    self.assertEqual((row["sold"], row["expected"], row["variance"]), ("24", "24", "0"))
                    con.execute("UPDATE cukcuk_invoice_items SET unit_name='' WHERE detail_id='detail-1'")
                    row = app.daily_stock_report(con, "2025-10-08")[0]
                    self.assertTrue(row["unit_unknown"])
                    self.assertIsNone(row["sold"])
                    self.assertIsNone(row["variance"])
        finally:
            app.DB = original_db

    def test_four_tab_groups_are_supported(self):
        self.assertTrue({"beer", "soft_drink", "water", "tobacco", "rice_paper", "peanuts",
                         "dry_good", "spice", "vegetable", "ice", "coal"}.issubset(app.ITEM_GROUPS))

    def test_ice_usage_is_daily_and_cannot_be_entered_twice(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("PRAGMA foreign_keys=OFF")
                    con.execute("INSERT INTO items(code,name,group_name,unit) VALUES(?,?,?,?)",
                                ("ICE", "Đá viên", "ice", "kg"))
                    handler = app.Handler.__new__(app.Handler)
                    user = {"id": 1, "role": "owner"}
                    payload = {"day": "2025-10-08", "item_id": 1, "quantity": "12.5", "note": "Ca tối"}
                    handler.mutate(con, user, "/api/daily-usage", payload)
                    stored = con.execute("SELECT quantity FROM daily_usage WHERE day=? AND item_id=?",
                                         ("2025-10-08", 1)).fetchone()[0]
                    self.assertEqual(stored, "12.5")
                    with self.assertRaises(app.ApiError):
                        handler.mutate(con, user, "/api/daily-usage", payload)
                    with self.assertRaises(app.ApiError):
                        handler.mutate(con, user, "/api/stock-moves",
                                       {"item_id": 1, "kind": "receipt", "quantity": "5"})
        finally:
            app.DB = original_db

    def test_bulk_count_requires_every_item_and_keeps_saved_values(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("PRAGMA foreign_keys=OFF")
                    con.execute("INSERT INTO items(code,name,group_name,unit,units_per_carton) VALUES(?,?,?,?,?)",
                                ("BEER", "Bia", "beer", "lon", 24))
                    con.execute("INSERT INTO items(code,name,group_name,unit,units_per_carton) VALUES(?,?,?,?,?)",
                                ("RICE", "Bánh tráng", "rice_paper", "gói", 10))
                    handler = app.Handler.__new__(app.Handler)
                    user = {"id": 1, "role": "owner"}
                    today = app.datetime.now(app.timezone(app.timedelta(hours=7))).date().isoformat()
                    payload = {"day": today, "phase": "opening", "items": [
                        {"item_id": 1, "cartons": "12"}, {"item_id": 2, "cartons": "0"}]}
                    self.assertEqual(handler.mutate(con, user, "/api/daily-stock-batch", {**payload, "items": payload["items"][:1]})["inserted"], 1)
                    self.assertEqual(handler.mutate(con, user, "/api/daily-stock-batch", payload)["inserted"], 1)
                    self.assertEqual(handler.mutate(con, user, "/api/daily-stock-batch", payload)["inserted"], 0)
                    handler.mutate(con, user, "/api/daily-stock-batch", {**payload, "items": [
                        {"item_id": 1, "cartons": "11"}, payload["items"][1]]})
                    self.assertEqual(con.execute("SELECT quantity FROM daily_stock_counts WHERE item_id=1").fetchone()[0], "264")
                    with self.assertRaises(app.ApiError):
                        handler.mutate(con, user, "/api/daily-stock-batch", {**payload, "day": "2025-10-08"})
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM daily_stock_counts").fetchone()[0], 2)
        finally:
            app.DB = original_db

    def test_carton_factor_is_required_for_positive_count_and_can_be_updated(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("PRAGMA foreign_keys=OFF")
                    con.execute("INSERT INTO items(code,name,group_name,unit) VALUES(?,?,?,?)",
                                ("B1", "Bia", "beer", "lon"))
                    handler = app.Handler.__new__(app.Handler)
                    user = {"id": 1, "role": "owner"}
                    day = app.datetime.now(app.timezone(app.timedelta(hours=7))).date().isoformat()
                    payload = {"day": day, "phase": "opening", "items": [{"item_id": 1, "cartons": "2"}]}
                    with self.assertRaises(app.ApiError):
                        handler.mutate(con, user, "/api/daily-stock-batch", payload)
                    handler.mutate(con, user, "/api/items/1/carton-size", {"units_per_carton": 20})
                    handler.mutate(con, user, "/api/daily-stock-batch", payload)
                    self.assertEqual(con.execute("SELECT quantity,cartons FROM daily_stock_counts").fetchone()[:],
                                     ("40", "2"))
                    handler.mutate(con, user, "/api/items/1/carton-size", {"units_per_carton": 24})
                    self.assertEqual(con.execute("SELECT quantity FROM daily_stock_counts").fetchone()[0], "48")
        finally:
            app.DB = original_db

    def test_new_saleable_item_is_created_with_carton_size(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("PRAGMA foreign_keys=OFF")
                    handler = app.Handler.__new__(app.Handler)
                    handler.mutate(con, {"id": 1, "role": "owner"}, "/api/items", {
                        "code": "NEW-DRINK", "name": "Nuoc moi", "group_name": "soft_drink",
                        "unit": "Lon", "units_per_carton": 24})
                    self.assertEqual(con.execute("SELECT units_per_carton FROM items WHERE code='NEW-DRINK'").fetchone()[0], 24)
        finally:
            app.DB = original_db

    def test_liquor_is_counted_by_carton_of_twelve_bottles(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("PRAGMA foreign_keys=OFF")
                    handler = app.Handler.__new__(app.Handler)
                    user = {"id": 1, "role": "owner"}
                    item = handler.mutate(con, user, "/api/items", {
                        "code": "WINE", "name": "Ruou", "group_name": "liquor", "unit": "Lon"})
                    item_id = item["id"]
                    saved = con.execute("SELECT unit,units_per_carton FROM items WHERE id=?", (item_id,)).fetchone()
                    self.assertEqual((saved["unit"], saved["units_per_carton"]), ("Chai", 12))
                    day = app.datetime.now(app.timezone(app.timedelta(hours=7))).date().isoformat()
                    payload = {"day": day, "phase": "opening", "items": [{"item_id": item_id, "cartons": "3"}]}
                    handler.mutate(con, user, "/api/daily-stock-batch", payload)
                    self.assertEqual(con.execute("SELECT quantity FROM daily_stock_counts WHERE item_id=?", (item_id,)).fetchone()[0], "36")
                    handler.mutate(con, user, f"/api/items/{item_id}/carton-size", {"units_per_carton": 24})
                    self.assertEqual(con.execute("SELECT quantity FROM daily_stock_counts WHERE item_id=?", (item_id,)).fetchone()[0], "72")
        finally:
            app.DB = original_db

    def test_tobacco_is_counted_by_tree_of_ten_packs(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("PRAGMA foreign_keys=OFF")
                    handler = app.Handler.__new__(app.Handler)
                    user = {"id": 1, "role": "owner"}
                    item_id = handler.mutate(con, user, "/api/items", {
                        "code": "TNn", "name": "Thuốc con ngựa", "group_name": "tobacco", "unit": "Gói"})["id"]
                    item = con.execute("SELECT unit,units_per_carton FROM items WHERE id=?", (item_id,)).fetchone()
                    self.assertEqual((item["unit"], item["units_per_carton"]), ("Gói", 10))
                    day = app.datetime.now(app.timezone(app.timedelta(hours=7))).date().isoformat()
                    handler.mutate(con, user, "/api/daily-stock-batch", {
                        "day": day, "phase": "opening", "items": [{"item_id": item_id, "cartons": "2", "loose_units": "1"}]})
                    handler.mutate(con, user, "/api/daily-stock-batch", {
                        "day": day, "phase": "closing", "items": [{"item_id": item_id, "cartons": "1", "loose_units": "3"}]})
                    counts = con.execute("SELECT phase,quantity FROM daily_stock_counts WHERE item_id=? ORDER BY phase", (item_id,)).fetchall()
                    self.assertEqual([(row["phase"], row["quantity"]) for row in counts],
                                     [("closing", "13"), ("opening", "21")])
        finally:
            app.DB = original_db

    def test_inline_stock_edits_today_without_creating_past_count(self):
        original_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    con.execute("PRAGMA foreign_keys=OFF")
                    handler = app.Handler.__new__(app.Handler)
                    user = {"id": 1, "role": "owner"}
                    item_id = handler.mutate(con, user, "/api/items", {
                        "code": "NEW-BEER", "name": "Bia moi", "group_name": "beer", "unit": "Lon"})["id"]
                    self.assertEqual(con.execute("SELECT units_per_carton FROM items WHERE id=?", (item_id,)).fetchone()[0], 24)
                    day = app.datetime.now(app.timezone(app.timedelta(hours=7))).date().isoformat()
                    for field, amount in (("previous_closing", "50"), ("incoming", "48")):
                        handler.mutate(con, user, "/api/daily-stock-inline", {
                            "day": day, "item_id": item_id, "field": field, "quantity": amount})
                    row = next(r for r in app.daily_stock_report(con, day) if r["id"] == item_id)
                    self.assertEqual((row["opening"], row["incoming"]), ("50", "48"))
                    self.assertEqual(con.execute("SELECT cartons FROM daily_stock_counts WHERE item_id=?", (item_id,)).fetchone()[0], "2")
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM daily_stock_counts WHERE day<>?", (day,)).fetchone()[0], 0)
                    with self.assertRaises(app.ApiError):
                        handler.mutate(con, user, "/api/daily-stock-inline", {
                            "day": "2025-10-08", "item_id": item_id,
                            "field": "previous_closing", "quantity": "12"})
        finally:
            app.DB = original_db


if __name__ == "__main__":
    unittest.main()
