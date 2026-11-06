"""Add the confirmed rows from the owner's CUKCUK menu screenshots once.

Existing rows are left untouched. Run locally; the command prints no menu data.
"""

import app
from menu_catalog import CODE_ALIASES, READY

REMOVED_CODES = ("BC", "BSG", "HOEGAARDEN", "HR", *CODE_ALIASES)
OWNER_CARTON_SIZE = {"HUCH": 20, "BULO": 28}

# Manufacturer documents identify these exact can/bottle variants as 24 units per carton/crate.
# Keep ambiguous products unset; the restaurant's actual supplier packaging takes precedence.
VERIFIED_CARTON_SIZE = {
    "BIAHENIKENCHAI": 24,
    "B3": 24,
    "TILU": 24,
    "COCA": 24,
    "FANTA": 24,
}


def seed(con):
    codes = [code for code, _, _, _ in READY]
    if len(codes) != len(set(codes)):
        raise ValueError("Duplicate code in menu seed")
    inserted = 0
    conflicts = 0
    con.execute("UPDATE items SET active=0 WHERE code IN (" + ",".join("?" for _ in REMOVED_CODES) + ")", REMOVED_CODES)
    for code, name, group, unit in READY:
        if group not in app.TRACKED_GROUPS or not 1 <= len(code) <= 40:
            raise ValueError("Invalid menu seed")
        existing = con.execute("SELECT name,group_name,unit,units_per_carton FROM items WHERE code=?", (code,)).fetchone()
        if existing:
            if (existing["name"], existing["group_name"], existing["unit"]) != (name, group, unit):
                conflicts += 1
            if code in OWNER_CARTON_SIZE:
                con.execute("UPDATE items SET units_per_carton=? WHERE code=?", (OWNER_CARTON_SIZE[code], code))
            elif group == "liquor":
                con.execute("UPDATE items SET units_per_carton=12,unit='Chai' WHERE code=?", (code,))
            elif group == "tobacco":
                con.execute("UPDATE items SET units_per_carton=10,unit='Gói' WHERE code=?", (code,))
            elif existing["units_per_carton"] is None:
                con.execute("UPDATE items SET units_per_carton=? WHERE code=?", (VERIFIED_CARTON_SIZE.get(code, 24), code))
            continue
        con.execute("INSERT INTO items(code,name,group_name,unit,min_stock,units_per_carton) VALUES(?,?,?,?,?,?)",
                    (code, name, group, unit, "0", 12 if group == "liquor" else 10 if group == "tobacco" else OWNER_CARTON_SIZE.get(code, VERIFIED_CARTON_SIZE.get(code, 24))))
        inserted += 1
    return inserted, conflicts


def main():
    if not app.DB.is_file():
        raise SystemExit("Database not found. Start the web app first.")
    with app.db() as con:
        inserted, conflicts = seed(con)
    print("MENU_SEED_OK" if not conflicts else "MENU_SEED_OK_WITH_EXISTING_DIFFERENCES")
    return inserted


if __name__ == "__main__":
    main()
