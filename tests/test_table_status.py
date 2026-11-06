import unittest

from table_merchandise import project_table_items, project_table_status


class TableStatusTest(unittest.TestCase):
    def test_every_open_table_is_shown_and_required_snacks_are_checked(self):
        orders = [
            {"Id": "order-2", "Status": 1, "TableName": "Bàn 2", "OrderDetails": [
                {"Id": 1, "ItemId": "beer-id", "ItemName": "Bia", "Quantity": 2},
                {"Id": 2, "ItemId": "rice-id", "ItemName": "Bánh tráng", "Quantity": 1},
            ]},
            {"Id": "order-4", "Status": 3, "TableName": "Bàn 4", "OrderDetails": []},
            {"Id": "order-paid", "Status": 4, "TableName": "Bàn 8", "OrderDetails": []},
            {"Id": "order-merged", "Status": 1, "TableName": "Bàn 5, 6", "OrderDetails": []},
        ]
        catalog = {"beer-id": "BEER", "rice-id": "RICE"}
        groups = {"BEER": "beer", "RICE": "rice_paper"}
        items, unmapped, unknown_tables = project_table_items(orders, catalog, groups)
        tables = {row["table"]: row for row in project_table_status(orders, items)}
        self.assertEqual(unmapped, 0)
        self.assertEqual(set(tables), {"Bàn 2", "Bàn 4", "Bàn 5, 6"})
        self.assertEqual(tables["Bàn 2"]["quantities"]["beer"], "2")
        self.assertEqual(tables["Bàn 2"]["missing_required"], ["peanuts"])
        self.assertEqual(tables["Bàn 4"]["missing_required"], ["rice_paper", "peanuts"])
        self.assertTrue(tables["Bàn 4"]["no_beer"])
        self.assertTrue(tables["Bàn 5, 6"]["combined_table"])


if __name__ == "__main__":
    unittest.main()
