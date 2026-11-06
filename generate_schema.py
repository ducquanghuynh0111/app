"""Regenerate schema.sql from the application's current table definitions."""

import re
import sqlite3
import tempfile
from pathlib import Path

import app


ROOT = Path(__file__).resolve().parent


def generate() -> int:
    original_database = app.DB
    with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
        app.DB = Path(temporary) / "schema_source.db"
        try:
            app.init_db()
        finally:
            app.DB = original_database
        connection = sqlite3.connect(Path(temporary) / "schema_source.db")
        try:
            statements = list(connection.iterdump())
            table_count = connection.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
        finally:
            connection.close()

    schema = [statement for statement in statements if not re.match(
        r"(?i)^\s*(?:INSERT|REPLACE|UPDATE|DELETE)\b", statement
    )]
    if table_count == 0 or not schema:
        raise RuntimeError("Không tạo được cấu trúc bảng")
    (ROOT / "schema.sql").write_text("\n".join(schema) + "\n", encoding="utf-8")
    return table_count


if __name__ == "__main__":
    print(f"Schema created: {generate()} tables")
