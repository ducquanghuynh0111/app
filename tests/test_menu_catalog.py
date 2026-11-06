import tempfile
import unittest
from pathlib import Path

import app
from menu_catalog import READY
from menu_catalog import CODE_ALIASES, canonical_code
from seed_menu_catalog import REMOVED_CODES, OWNER_CARTON_SIZE
from seed_menu_catalog import seed


class MenuCatalogTest(unittest.TestCase):
    def test_seed_is_idempotent_and_preserves_codes_with_spaces(self):
        previous_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    first = seed(con)
                    second = seed(con)
                    self.assertEqual(first, (len(READY), 0))
                    self.assertEqual(second, (0, 0))
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM items").fetchone()[0], len(READY))
                    self.assertEqual(con.execute("SELECT units_per_carton FROM items WHERE code=?", ("B3",)).fetchone()[0], 24)
                    con.execute("UPDATE items SET units_per_carton=20 WHERE code='B3'")
                    self.assertEqual(seed(con), (0, 0))
                    self.assertEqual(con.execute("SELECT units_per_carton FROM items WHERE code='B3'").fetchone()[0], 20)
                    self.assertEqual(con.execute("SELECT group_name FROM items WHERE code=?", ("7 UP",)).fetchone()[0],
                                     "soft_drink")
                    for code, factor in OWNER_CARTON_SIZE.items():
                        self.assertEqual(con.execute("SELECT units_per_carton FROM items WHERE code=?", (code,)).fetchone()[0], factor)
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM items WHERE group_name='liquor' AND units_per_carton=12 AND unit='Chai'").fetchone()[0], 5)
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM items WHERE code IN ('BATR','DAUPHONG') AND active=1 AND units_per_carton=24").fetchone()[0], 2)
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM items WHERE code='BATR' AND group_name='rice_paper'").fetchone()[0], 1)
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM items WHERE code='DAUPHONG' AND group_name='peanuts'").fetchone()[0], 1)
                    self.assertEqual({canonical_code(code): code for code in ('DG','DAUPHONG','COCA','HUCH','BH')},
                                     {code: code for code in ('DG','DAUPHONG','COCA','HUCH','BH')})
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM items WHERE code IN ('TNn','TM') AND group_name='tobacco' AND unit='Gói' AND units_per_carton=10 AND active=1").fetchone()[0], 2)
        finally:
            app.DB = previous_db

    def test_seed_deactivates_removed_products_without_deleting_history(self):
        previous_db = app.DB
        try:
            with tempfile.TemporaryDirectory() as directory:
                app.DB = Path(directory) / "restaurant.db"
                app.init_db()
                with app.db() as con:
                    for code in REMOVED_CODES:
                        con.execute("INSERT INTO items(code,name,group_name,unit,min_stock) VALUES(?,?,?,?,?)",
                                    (code, code, "beer", "Lon", "0"))
                    seed(con)
                    placeholders = ",".join("?" for _ in REMOVED_CODES)
                    self.assertEqual(con.execute(f"SELECT COUNT(*) FROM items WHERE code IN ({placeholders}) AND active=0", REMOVED_CODES).fetchone()[0], len(REMOVED_CODES))
                    self.assertEqual(con.execute(f"SELECT COUNT(*) FROM items WHERE code IN ({placeholders})", REMOVED_CODES).fetchone()[0], len(REMOVED_CODES))
                    self.assertTrue(set(CODE_ALIASES).issubset(REMOVED_CODES))
        finally:
            app.DB = previous_db


if __name__ == "__main__":
    unittest.main()
