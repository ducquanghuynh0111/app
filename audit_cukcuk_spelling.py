"""Read-only candidate audit of CUKCUK item names; no data is written."""

import json
import re
import unicodedata
from collections import defaultdict

from cukcuk_sync import Client


def plain(text):
    value = unicodedata.normalize("NFKD", text.casefold().replace("đ", "d"))
    return "".join(char for char in value if not unicodedata.combining(char))


def candidates(rows):
    names = [(str(row.get("Name") or row.get("ItemName") or "").strip(),
              str(row.get("Code") or row.get("ItemCode") or "").strip()) for row in rows]
    words = defaultdict(set)
    for name, _ in names:
        for word in re.findall(r"[\w]+", name, re.UNICODE):
            if len(word) >= 2 and plain(word) != word.casefold():
                words[plain(word)].add(word.casefold())
    no_marks = []
    mixed = []
    for name, code in names:
        if not name or name.casefold() in {"bỏ", "bo", "phụ thu", "phụ thu chế biến"}:
            continue
        if name.isascii() and re.search(r"[A-Za-z]", name):
            no_marks.append({"name": name, "code": code})
            continue
        suspect = sorted({word for word in re.findall(r"[A-Za-z]+", name)
                          if len(word) >= 2 and plain(word) in words})
        if suspect:
            mixed.append({"name": name, "code": code, "plain_words": suspect})
    no_marks.sort(key=lambda item: plain(item["name"]))
    mixed.sort(key=lambda item: plain(item["name"]))
    return no_marks, mixed


def main():
    rows = list(Client.from_environment().inventory_items())
    no_marks, mixed = candidates(rows)
    print(json.dumps({"total_items": len(rows), "no_marks": no_marks,
                      "mixed_candidates": mixed}, ensure_ascii=False))


if __name__ == "__main__":
    main()
