"""Import a schema-only SQL file into a new SQLite database."""

import argparse
import os
import re
import sqlite3
import tempfile
from pathlib import Path


def import_database(source: Path, destination: Path) -> None:
    source = source.resolve()
    destination = destination.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Không tìm thấy bản xuất SQL: {source}")
    if destination.exists():
        raise FileExistsError(f"Cơ sở dữ liệu đã tồn tại, không ghi đè: {destination}")
    schema = source.read_text(encoding="utf-8")
    if re.search(r"(?im)^\s*(?:INSERT|REPLACE|UPDATE|DELETE)\b", schema):
        raise ValueError("Tệp SQL chứa dữ liệu; chỉ được nhập cấu trúc bảng")
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".db.tmp", dir=destination.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    connection = None
    try:
        connection = sqlite3.connect(temporary_path)
        connection.executescript(schema)
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Bản SQL không khôi phục được cơ sở dữ liệu toàn vẹn")
        connection.close()
        connection = None
        if destination.exists():
            raise FileExistsError(f"Cơ sở dữ liệu đã tồn tại, không ghi đè: {destination}")
        os.replace(temporary_path, destination)
    finally:
        if connection is not None:
            connection.close()
        temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql", type=Path, default=Path("schema.sql"))
    parser.add_argument("--db", type=Path, default=Path("data/restaurant.db"))
    args = parser.parse_args()
    import_database(args.sql, args.db)
    print(f"Database imported: {args.db.resolve()}")
