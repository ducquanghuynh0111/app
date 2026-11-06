"""Set up an empty SQLite database, then start the restaurant app."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from import_database import import_database


ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "schema.sql"
DATABASE = ROOT / "data" / "restaurant.db"


def install() -> bool:
    if sys.version_info < (3, 11):
        raise RuntimeError("Cần Python 3.11 trở lên")
    if not SCHEMA.is_file():
        raise FileNotFoundError("Thiếu schema.sql trong thư mục ứng dụng")
    if not (ROOT / "static" / "index.html").is_file():
        raise FileNotFoundError("Thiếu giao diện static/index.html")
    schema = SCHEMA.read_text(encoding="utf-8")
    if re.search(r"(?im)^\s*(?:INSERT|REPLACE|UPDATE|DELETE)\b", schema):
        raise ValueError("schema.sql chứa lệnh dữ liệu; bộ cài chỉ chấp nhận cấu trúc bảng")
    if DATABASE.exists():
        print("Database already exists; existing data was kept.")
        return False
    import_database(SCHEMA, DATABASE)
    print("Empty SQLite database created from schema.sql.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup-only", action="store_true", help="Create tables without starting the web app")
    args = parser.parse_args()
    install()
    if not args.setup_only:
        print("Starting web app at http://127.0.0.1:8000")
        subprocess.run([sys.executable, str(ROOT / "app.py")], cwd=ROOT, check=True)
