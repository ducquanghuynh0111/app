"""Read CUKCUK menu and print only duplicate item names with their codes."""

import json
import re
import unicodedata
from collections import defaultdict

from cukcuk_sync import Client


def name_key(value):
    text = unicodedata.normalize("NFKD", value.casefold().replace("đ", "d"))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def duplicate_names(rows):
    grouped = defaultdict(list)
    missing_names = 0
    for row in rows:
        name = str(row.get("Name") or row.get("ItemName") or row.get("InventoryItemName") or "").strip()
        if not name:
            missing_names += 1
            continue
        code = str(row.get("Code") or row.get("ItemCode") or "").strip()
        grouped[name_key(name)].append((name, code))
    duplicates = []
    for records in grouped.values():
        if len(records) < 2:
            continue
        names = sorted({name for name, _ in records}, key=str.casefold)
        codes = sorted({code or "(không mã)" for _, code in records}, key=str.casefold)
        duplicates.append({"name": names[0], "name_variants": names,
                           "codes": codes, "rows": len(records)})
    duplicates.sort(key=lambda item: name_key(item["name"]))
    return duplicates, missing_names


def main():
    rows = list(Client.from_environment().inventory_items())
    duplicates, missing_names = duplicate_names(rows)
    print(json.dumps({"total_items": len(rows), "missing_name_rows": missing_names,
                      "duplicate_groups": duplicates}, ensure_ascii=False))


if __name__ == "__main__":
    main()
