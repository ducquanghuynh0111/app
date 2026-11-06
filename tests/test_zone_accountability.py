import unittest

from zone_accountability import build_live_review, compare_observation, staff_at, table_number


class ZoneAccountabilityTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "as_of": "2026-11-06T12:00:00Z",
            "tables": [
                {"table": "Bàn 2", "combined_table": False, "mapping_status": "mapped",
                 "no_beer": True, "missing_required": ["peanuts"],
                 "quantities": {"beer": 0, "rice_paper": 1, "peanuts": 0}},
                {"table": "Bàn 4", "combined_table": False, "mapping_status": "mapped",
                 "no_beer": False, "missing_required": [],
                 "quantities": {"beer": 2, "water": 1}},
            ],
            "rows": [
                {"table": "Bàn 2", "group": "rice_paper", "quantity": 1},
                {"table": "Bàn 4", "group": "beer", "quantity": 2},
                {"table": "Bàn 4", "group": "soft_drink", "quantity": 1},
            ],
        }

    def test_live_review_adds_zone_staff_and_missing_groups(self):
        assignments = [{"zone_id": 3, "user_id": 8, "user_name": "Phục vụ A",
                        "active": 1, "starts_at": "2026-11-06T10:00:00Z",
                        "ends_at": "2026-11-06T20:00:00Z"}]
        result = build_live_review(self.report, [{"id": 3, "name": "Khu A", "active": 1}],
                                   [{"table_name": "Bàn 2", "zone_id": 3}], assignments)
        self.assertEqual(result[0]["zone_name"], "Khu A")
        self.assertEqual(result[0]["staff"], [{"id": 8, "name": "Phục vụ A"}])
        self.assertEqual(result[0]["missing_order_groups"], ["beer", "peanuts"])
        self.assertIsNone(result[1]["zone_name"])
        self.assertEqual(result[1]["staff"], [])

    def test_numeric_table_name_matches_cukcuk_label(self):
        self.assertEqual(table_number("Bàn 002"), "2")
        self.assertEqual(table_number("2"), "2")
        self.assertIsNone(table_number("Bàn 0"))
        self.assertIsNone(table_number("Bàn A"))
        result = build_live_review(self.report, [{"id": 3, "name": "Nhân viên A", "active": 1}],
                                   [{"table_name": "2", "zone_id": 3}], [])
        self.assertEqual(result[0]["zone_name"], "Nhân viên A")

    def test_live_review_keeps_beer_name_and_converted_unit(self):
        self.report["rows"].append({"table": "Bàn 4", "group": "beer", "code": "BT", "name": "Bia Tiger",
                                     "quantity": "24", "unit": "Lon", "unit_status": "known"})
        result = build_live_review(self.report, [], [], [], {"BT": 24})
        tiger = next(item for item in result[1]["beer_items"] if item["code"] == "BT")
        self.assertEqual((tiger["name"], tiger["quantity"], tiger["unit"], tiger["units_per_carton"]),
                         ("Bia Tiger", "24", "Lon", 24))

    def test_live_review_keeps_water_and_tobacco_by_product(self):
        self.report["rows"].extend([
            {"table":"Bàn 4","group":"soft_drink","code":"PEPSI","name":"Pepsi",
             "quantity":"2","unit":"Lon","unit_status":"known"},
            {"table":"Bàn 4","group":"tobacco","code":"TNN","name":"Thuốc con ngựa",
             "quantity":"10","unit":"Gói","unit_status":"known"},
        ])
        result = build_live_review(self.report, [], [], [], {"PEPSI":24,"TNN":10})
        products = {item["code"]:item for item in result[1]["product_items"]}
        self.assertEqual((products["PEPSI"]["group"],products["PEPSI"]["units_per_carton"]),("water",24))
        self.assertEqual((products["TNN"]["group"],products["TNN"]["units_per_carton"]),("tobacco",10))

    def test_staff_assignment_respects_time_and_deduplicates(self):
        row = {"zone_id": 3, "user_id": 8, "user_name": "Phục vụ A", "active": 1,
               "starts_at": "2026-11-06T10:00:00Z", "ends_at": "2026-11-06T20:00:00Z"}
        self.assertEqual(len(staff_at([row, row], 3, "2026-11-06T12:00:00Z")), 1)
        self.assertEqual(staff_at([row], 3, "2026-11-06T20:00:00Z"), [])

    def test_manual_comparison_uses_only_entered_groups(self):
        lines, status = compare_observation(self.report, "Bàn 4", {"beer": 3, "water": 1})
        self.assertEqual(status, "mapped")
        self.assertEqual(lines, [
            {"group": "beer", "observed_qty": "3", "ordered_qty": "2", "surplus_qty": "1"},
            {"group": "water", "observed_qty": "1", "ordered_qty": "1", "surplus_qty": "0"},
        ])

    def test_unknown_mapping_never_claims_surplus(self):
        self.report["tables"][0]["mapping_status"] = "unknown"
        lines, status = compare_observation(self.report, "Bàn 2", {"beer": 4})
        self.assertEqual(status, "unknown")
        self.assertIsNone(lines[0]["ordered_qty"])
        self.assertIsNone(lines[0]["surplus_qty"])

    def test_closed_table_and_fractional_actual_rejected(self):
        with self.assertRaises(ValueError):
            compare_observation(self.report, "Bàn 9", {"beer": 1})
        with self.assertRaises(ValueError):
            compare_observation(self.report, "Bàn 4", {"beer": 1.5})


if __name__ == "__main__":
    unittest.main()
