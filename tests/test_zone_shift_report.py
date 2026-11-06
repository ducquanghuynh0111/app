import unittest

from zone_shift_report import business_day, project_invoices, reconcile_stock, tobacco_balance


class ZoneShiftReportTests(unittest.TestCase):
    def setUp(self):
        self.items = [
            {"code": "BT", "name": "Bia Tiger", "group_name": "beer", "unit": "Lon", "units_per_carton": 24},
            {"code": "TNN", "name": "Thuốc con ngựa", "group_name": "tobacco", "unit": "Gói", "units_per_carton": 10},
            {"code": "BATR", "name": "Bánh tráng", "group_name": "rice_paper", "unit": "Gói", "units_per_carton": None},
            {"code": "DAUPHONG", "name": "Đậu phộng", "group_name": "peanuts", "unit": "Gói", "units_per_carton": None},
        ]
        self.zones = [{"id": 1, "name": "An", "active": 1}]
        self.tables = [{"table_name": "1", "zone_id": 1}, {"table_name": "2", "zone_id": 1}]

    def invoice(self, ref, table, details, status=3, moment="2026-11-06T23:30:00+07:00"):
        return {"RefId": ref, "RefNo": ref, "RefDate": moment, "PaymentStatus": status,
                "OrderType": 1, "TableName": table,
                "SAInvoiceDetails": [{"ItemCode": code, "UnitName": unit, "Quantity": qty}
                                     for code, unit, qty in details]}

    def test_conversion_and_per_invoice_missing_at_reused_table(self):
        invoices = [
            self.invoice("a", "Bàn 1", [("BT", "Thùng", 1), ("TNN", "Cây", 1)]),
            self.invoice("b", "1", [("BT", "Lon", 2), ("BATR", "Gói", 1), ("DAPH", "Gói", 1)]),
            self.invoice("c", "Bàn 2", [("DAPH", "Gói", 1)]),
            self.invoice("d", "Bàn 1", [("BT", "Lon", 99)], status=0),
        ]
        result = project_invoices(invoices, "2026-11-06", self.zones, self.tables, self.items)
        self.assertEqual(result["sold"]["BT"], "26")
        self.assertEqual(result["sold"]["TNN"], "10")
        self.assertEqual(result["sold"]["DAUPHONG"], "2")
        self.assertEqual(result["invoice_count"], 3)
        beer = next(item for item in result["zones"][0]["items"] if item["code"] == "BT")
        self.assertEqual(beer["packs"], "1 thùng + 2 lon")
        self.assertEqual(next(w for w in result["warnings"] if w["invoice_id"] == "a")["missing"],
                         ["Bánh tráng", "Đậu phộng"])
        self.assertEqual(next(w for w in result["warnings"] if w["invoice_id"] == "c")["missing"],
                         ["Bia", "Bánh tráng"])
        self.assertFalse(any(w["invoice_id"] == "b" for w in result["warnings"]))
        self.assertEqual([row["invoice_id"] for row in result["closed_invoices"]], ["a", "b", "c"])
        self.assertEqual([row["table"] for row in result["closed_invoices"][:2]], ["1", "1"])
        self.assertEqual(result["closed_invoices"][0]["items"][0]["quantity"], "1")
        self.assertEqual(result["closed_invoices"][0]["invoice_at"], "2026-11-06T23:30:00+07:00")

    def test_closed_invoice_keeps_non_inventory_dishes_without_customer_data(self):
        invoice = self.invoice("paid", "Bàn 2", [("BT", "Lon", 2), ("MONAN", "Phần", 3)])
        invoice["SAInvoiceDetails"][1]["ItemName"] = "Mì xào"
        invoice["CustomerName"] = "Tên khách riêng tư"
        result = project_invoices([invoice], "2026-11-06", self.zones, self.tables, self.items)
        rows = result["closed_invoices"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["items"][1], {"name": "Mì xào", "quantity": "3", "unit": "Phần"})
        self.assertNotIn("CustomerName", str(rows))

    def test_cross_midnight_and_uncertain_item(self):
        self.assertEqual(business_day("2026-11-07T01:00:00+07:00"), "2026-11-06")
        result = project_invoices([self.invoice("a", "Bàn 1", [("UNKNOWN", "Lon", 1)],
                                               moment="2026-11-07T01:00:00+07:00")],
                                  "2026-11-06", self.zones, self.tables, self.items)
        self.assertEqual(result["unmapped_codes"], ["UNKNOWN"])
        self.assertTrue(result["warnings"][0]["uncertain"])

    def test_old_coca_code_counts_under_canonical_code(self):
        items = self.items + [{"code": "COCA", "name": "Coca", "group_name": "soft_drink",
                               "unit": "Lon", "units_per_carton": 24}]
        invoices = [self.invoice("old", "Bàn 1", [("CC", "Lon", 2)])]
        result = project_invoices(invoices, "2026-11-06", self.zones, self.tables, items)
        self.assertEqual(result["sold"]["COCA"], "2")
        self.assertNotIn("CC", result["sold"])

    def test_old_huda_codes_count_under_selected_codes(self):
        items = self.items + [
            {"code": "HUCH", "name": "HUDA CHAI", "group_name": "beer", "unit": "Chai", "units_per_carton": 20},
            {"code": "BH", "name": "BIA HUDA", "group_name": "beer", "unit": "Lon", "units_per_carton": 24},
        ]
        invoices = [self.invoice("old", "Bàn 1", [("BIAHUDACHAI", "Chai", 2), ("HL", "Chai", 3)])]
        result = project_invoices(invoices, "2026-11-06", self.zones, self.tables, items)
        self.assertEqual(result["sold"]["HUCH"], "2")
        self.assertEqual(result["sold"]["BH"], "3")

    def test_stock_and_tobacco_reconciliation(self):
        row = {"code": "BT", "name": "Tiger", "group": "beer", "unit": "Lon",
               "opening": "24", "incoming": "24", "received": "24", "waste_gift": "0",
               "closing": "22", "has_previous_closing": True}
        self.assertEqual(reconcile_stock([row], {"BT": "26"}, set())[0]["status"], "ok")
        row["has_previous_closing"] = False
        self.assertEqual(reconcile_stock([row], {"BT": "26"}, set())[0]["status"], "unknown")
        self.assertEqual(tobacco_balance("20", "5", "5", "10"), "0")
        self.assertIsNone(tobacco_balance("20", None, "5", "10"))


if __name__ == "__main__":
    unittest.main()
