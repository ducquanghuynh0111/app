import unittest

from table_merchandise import project_table_items, project_table_status


class TableMerchandiseTests(unittest.TestCase):
    def test_water_and_tobacco_cartons_convert_to_base_units(self):
        orders = [{"Id": "one", "Status": 1, "TableName": "Bàn 1", "OrderDetails": [
            {"Id": "w1", "ItemId": "water", "ItemName": "Nước suối", "UnitName": "Thùng", "Quantity": 1},
            {"Id": "w2", "ItemId": "water", "ItemName": "Nước suối", "UnitName": "Chai", "Quantity": 2},
            {"Id": "s1", "ItemId": "soda", "ItemName": "Pepsi", "UnitName": "Lon", "Quantity": 2},
            {"Id": "t1", "ItemId": "tobacco", "ItemName": "Thuốc con ngựa", "UnitName": "Cây", "Quantity": 1},
        ]}]
        rows, unmapped, unknown = project_table_items(orders,
            {"water": "NS", "soda": "PEPSI", "tobacco": "TNN"},
            {"NS": "water", "PEPSI": "soft_drink", "TNN": "tobacco"},
            {"NS": 24, "PEPSI": 24, "TNN": 10},
            {"NS": "Chai", "PEPSI": "Lon", "TNN": "Gói"})
        self.assertEqual(unmapped, 0)
        self.assertEqual(unknown, set())
        self.assertEqual({row["code"]: row["quantity"] for row in rows},
                         {"NS": "26", "PEPSI": "2", "TNN": "10"})

    def test_beer_carton_and_cans_convert_to_cans_before_table_total(self):
        orders = [{"Id": "one", "Status": 1, "TableName": "Bàn 1", "OrderDetails": [
            {"Id": "carton", "ItemId": "tiger", "ItemName": "Bia Tiger", "UnitName": "Thùng", "Quantity": 1},
            {"Id": "can", "ItemId": "tiger", "ItemName": "Bia Tiger", "UnitName": "Lon", "Quantity": 2},
        ]}]
        rows, unmapped, unknown_tables = project_table_items(
            orders, {"tiger": "BT"}, {"BT": "beer"}, {"BT": 24}, {"BT": "Lon"})
        status = project_table_status(orders, rows, unknown_tables)[0]
        self.assertEqual(unmapped, 0)
        self.assertEqual(unknown_tables, set())
        self.assertEqual(status["quantities"]["beer"], "26")
        self.assertEqual({(row["name"], row["unit"]): row["quantity"] for row in rows},
                         {("Bia Tiger", "Lon"): "26"})

    def test_carton_without_pack_size_does_not_claim_can_quantity(self):
        orders = [{"Id": "one", "Status": 1, "TableName": "Bàn 1", "OrderDetails": [
            {"Id": "carton", "ItemId": "tiger", "ItemName": "Bia Tiger", "UnitName": "Thùng", "Quantity": 1},
        ]}]
        rows, _, unknown_tables = project_table_items(
            orders, {"tiger": "BT"}, {"BT": "beer"}, {}, {"BT": "Lon"})
        self.assertEqual(rows[0]["unit_status"], "unknown")
        self.assertEqual(unknown_tables, {"Bàn 1"})

    def test_same_item_across_orders_is_grouped_by_table_without_double_count(self):
        orders = [
            {"Id": "a", "Status": 1, "TableName": "Bàn 2", "OrderDetails": [
                {"Id": "a1", "ItemId": "beer-id", "ItemName": "Bia", "Quantity": 2},
                {"Id": "a1", "ItemId": "beer-id", "ItemName": "Bia", "Quantity": 2},
                {"Id": "a2", "ItemId": "snack-id", "ItemName": "Đậu phộng", "Quantity": 1},
            ]},
            {"Id": "b", "Status": 1, "TableName": "Bàn 4", "OrderDetails": [
                {"Id": "b1", "ItemId": "beer-id", "ItemName": "Bia", "Quantity": 3},
            ]},
        ]
        rows, unmapped, unknown_tables = project_table_items(
            orders, {"beer-id": "BIA-01", "snack-id": "DAU-01"},
            {"BIA-01": "beer", "DAU-01": "peanuts"},
        )
        self.assertEqual(unmapped, 0)
        self.assertEqual(unknown_tables, set())
        self.assertEqual({(r["table"], r["code"]): r["quantity"] for r in rows}, {
            ("Bàn 2", "BIA-01"): "2", ("Bàn 2", "DAU-01"): "1",
            ("Bàn 4", "BIA-01"): "3",
        })

    def test_paid_orders_additions_and_unmapped_items_are_not_counted(self):
        orders = [
            {"Id": "paid", "Status": 4, "TableName": "Bàn 1", "OrderDetails": [
                {"Id": "x", "ItemId": "beer-id", "Quantity": 3}]},
            {"Id": "live", "Status": 1, "TableName": "Bàn 2, Bàn 3", "OrderDetails": [
                {"Id": "y", "ItemId": "beer-id", "ItemName": "Bia", "Quantity": "1.5"},
                {"Id": "z", "ItemId": "unknown", "ItemName": "Nước", "Quantity": 1},
                {"Id": "opt", "ItemId": "beer-id", "ParentId": "y", "Quantity": 2},
            ]},
        ]
        rows, unmapped, unknown_tables = project_table_items(
            orders, {"beer-id": "BIA-01"}, {"BIA-01": "beer"})
        self.assertEqual(rows[0]["table"], "Bàn 2, Bàn 3")
        self.assertEqual(rows[0]["quantity"], "1.5")
        self.assertEqual(unmapped, 1)
        self.assertEqual(unknown_tables, {"Bàn 2, Bàn 3"})

    def test_liquor_does_not_replace_beer_for_table_alert(self):
        orders = [{"Id": "one", "Status": 1, "TableName": "Ban 5", "OrderDetails": [
            {"Id": "one-detail", "ItemId": "liquor-id", "ItemName": "Ruou", "Quantity": 2}]}]
        rows, unmapped, unknown_tables = project_table_items(
            orders, {"liquor-id": "RTM"}, {"RTM": "liquor"})
        status = project_table_status(orders, rows)
        self.assertEqual(unmapped, 0)
        self.assertEqual(status[0]["quantities"]["liquor"], "2")
        self.assertTrue(status[0]["no_beer"])
        self.assertEqual(unknown_tables, set())

    def test_both_peanut_codes_count_together_under_canonical_code(self):
        orders = [{"Id": "one", "Status": 1, "TableName": "Bàn 7", "OrderDetails": [
            {"Id": "a", "ItemId": "rice-id", "ItemName": "Bánh tráng", "Quantity": 1},
            {"Id": "b", "ItemId": "peanut-1", "ItemName": "Đậu phộng", "Quantity": 1},
            {"Id": "c", "ItemId": "peanut-2", "ItemName": "Đậu phộng", "Quantity": 2}]}]
        catalog = {"rice-id": "BATR", "peanut-1": "DAUPHONG", "peanut-2": "DAPH"}
        groups = {"BATR": "rice_paper", "DAUPHONG": "peanuts"}
        rows, unmapped, unknown_tables = project_table_items(orders, catalog, groups)
        status = project_table_status(orders, rows, unknown_tables)[0]
        self.assertEqual(unmapped, 0)
        self.assertEqual(status["quantities"]["peanuts"], "3")
        self.assertEqual(status["missing_required"], [])
        self.assertEqual({r["code"] for r in rows}, {"BATR", "DAUPHONG"})

    def test_old_huda_lon_code_uses_canonical_name_and_unit(self):
        orders = [{"Id": "one", "Status": 1, "TableName": "Bàn 3", "OrderDetails": [
            {"Id": "a", "ItemId": "old", "ItemName": "HUDA LON", "UnitName": "Chai", "Quantity": 1},
            {"Id": "b", "ItemId": "new", "ItemName": "BIA HUDA", "UnitName": "Lon", "Quantity": 2}]}]
        rows, unmapped, _ = project_table_items(orders, {"old": "HL", "new": "BH"},
            {"BH": "beer"}, {"BH": 24}, {"BH": "Lon"}, {"BH": "BIA HUDA"})
        self.assertEqual(unmapped, 0)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["code"], rows[0]["name"], rows[0]["unit"], rows[0]["quantity"]),
                         ("BH", "BIA HUDA", "Lon", "3"))

    def test_missing_catalog_id_marks_table_unknown(self):
        orders = [{"Id": "one", "Status": 1, "TableName": "Bàn 9", "OrderDetails": [
            {"Id": "a", "ItemId": "unmapped-id", "ItemName": "Không rõ", "Quantity": 1}]}]
        rows, unmapped, unknown_tables = project_table_items(orders, {}, {})
        status = project_table_status(orders, rows, unknown_tables)[0]
        self.assertEqual(unmapped, 1)
        self.assertEqual(status["mapping_status"], "unknown")


if __name__ == "__main__":
    unittest.main()
