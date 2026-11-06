"""Local restaurant control pilot. Python 3.11+, standard library only."""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import ssl
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "restaurant.db"
STATIC = ROOT / "static"
ROLES = {"owner", "manager", "cashier", "stock", "staff"}
DEPARTMENTS = {"management", "service", "kitchen", "runner", "cashier", "other"}
from table_merchandise import ACTIVE_ORDER_STATUSES, TRACKED_GROUPS, project_table_items, project_table_status
from menu_catalog import canonical_code
from zone_accountability import (CHECK_GROUPS, build_live_review, compare_observation,
    config_snapshot, init_zone_db, staff_at, table_number)
from zone_shift_report import (business_day, init_db as init_zone_shift_db,
    project_invoices, reconcile_stock, tobacco_balance, converted_quantity,
    number as shift_number, fmt as shift_fmt)
from saleable_history import history_report

ITEM_GROUPS = TRACKED_GROUPS | {"ingredient", "sauce", "spice", "dry_good", "vegetable", "ice", "coal", "other"}
DAILY_USAGE_GROUPS = {"ice", "coal"}
TABLE_STOCK_CACHE: dict = {}
TABLE_STOCK_LOCK = threading.Lock()
MONEY_LIMIT = 10**12
KIOSK_ATTEMPTS: dict[str, list[datetime]] = {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def db():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    try:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA journal_mode=WAL")
        yield con
        con.commit()
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    with db() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users(
              id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
              display_name TEXT NOT NULL, role TEXT NOT NULL,
              department TEXT NOT NULL DEFAULT 'other',
              password_hash TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS sessions(
              token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
              csrf TEXT NOT NULL, expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cash_shifts(
              id INTEGER PRIMARY KEY, label TEXT NOT NULL, opened_at TEXT NOT NULL,
              opened_by INTEGER NOT NULL REFERENCES users(id),
              opening_cash INTEGER NOT NULL DEFAULT 0,
              manual_cash INTEGER NOT NULL DEFAULT 0, manual_bank INTEGER NOT NULL DEFAULT 0,
              counted_cash INTEGER, counted_bank INTEGER, note TEXT NOT NULL DEFAULT '',
              locked_at TEXT, locked_by INTEGER REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS cash_entries(
              id INTEGER PRIMARY KEY, shift_id INTEGER NOT NULL REFERENCES cash_shifts(id),
              kind TEXT NOT NULL CHECK(kind IN ('income','expense','refund')),
              amount INTEGER NOT NULL CHECK(amount > 0), method TEXT NOT NULL
                CHECK(method IN ('cash','bank')), note TEXT NOT NULL,
              reference TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
              created_by INTEGER NOT NULL REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS items(
              id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
              group_name TEXT NOT NULL, unit TEXT NOT NULL,
              min_stock TEXT NOT NULL DEFAULT '0', active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS stock_moves(
              id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL REFERENCES items(id),
              quantity TEXT NOT NULL, kind TEXT NOT NULL, reason TEXT NOT NULL,
              reference TEXT NOT NULL DEFAULT '', shift_id INTEGER REFERENCES cash_shifts(id),
              created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS stock_counts(
              id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL REFERENCES items(id),
              book_qty TEXT NOT NULL, counted_qty TEXT NOT NULL,
              difference TEXT NOT NULL, note TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending',
              created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id),
              reviewed_at TEXT, reviewed_by INTEGER REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS work_shifts(
              id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
              starts_at TEXT NOT NULL, ends_at TEXT NOT NULL,
              checked_in_at TEXT, checked_out_at TEXT,
              note TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS order_incidents(
              id INTEGER PRIMARY KEY, bill_ref TEXT NOT NULL, category TEXT NOT NULL,
              description TEXT NOT NULL, amount INTEGER NOT NULL DEFAULT 0,
              user_id INTEGER REFERENCES users(id),
              status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL,
              created_by INTEGER NOT NULL REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS sales_imports(
              id INTEGER PRIMARY KEY, source_row_id TEXT NOT NULL UNIQUE,
              shift_id INTEGER NOT NULL REFERENCES cash_shifts(id),
              item_id INTEGER REFERENCES items(id),
              quantity TEXT NOT NULL, amount INTEGER NOT NULL,
              method TEXT NOT NULL CHECK(method IN ('cash','bank')),
              created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS audit_log(
              id INTEGER PRIMARY KEY, actor_id INTEGER REFERENCES users(id),
              action TEXT NOT NULL, entity TEXT NOT NULL, entity_id INTEGER,
              detail TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS kiosk_pins(
              user_id INTEGER PRIMARY KEY REFERENCES users(id), pin_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS daily_stock_counts(
              day TEXT NOT NULL, phase TEXT NOT NULL CHECK(phase IN ('opening','closing')),
              item_id INTEGER NOT NULL REFERENCES items(id), quantity TEXT NOT NULL,
              created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id),
              PRIMARY KEY(day,phase,item_id)
            );
            CREATE TABLE IF NOT EXISTS daily_stock_opening_overrides(
              day TEXT NOT NULL, item_id INTEGER NOT NULL REFERENCES items(id),
              quantity TEXT NOT NULL, created_at TEXT NOT NULL,
              created_by INTEGER NOT NULL REFERENCES users(id),
              PRIMARY KEY(day,item_id)
            );
            CREATE TABLE IF NOT EXISTS daily_usage(
              day TEXT NOT NULL, item_id INTEGER NOT NULL REFERENCES items(id),
              quantity TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id),
              PRIMARY KEY(day,item_id)
            );
            CREATE TABLE IF NOT EXISTS recipes(
              item_code TEXT NOT NULL, ingredient_id INTEGER NOT NULL REFERENCES items(id),
              quantity_per_unit TEXT NOT NULL, PRIMARY KEY(item_code,ingredient_id)
            );
            CREATE TABLE IF NOT EXISTS cukcuk_sync_runs(
              id INTEGER PRIMARY KEY, from_date TEXT NOT NULL, to_date TEXT NOT NULL,
              completed_at TEXT NOT NULL, invoice_count INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runner_orders(
              order_id TEXT PRIMARY KEY, order_no TEXT NOT NULL, table_name TEXT NOT NULL,
              order_status INTEGER NOT NULL, last_seen_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runner_items(
              detail_id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES runner_orders(order_id),
              item_name TEXT NOT NULL, item_key TEXT, quantity TEXT NOT NULL,
              source_quantity TEXT NOT NULL, served_quantity TEXT NOT NULL DEFAULT '0',
              first_seen_at TEXT NOT NULL,
              served_at TEXT, canceled_at TEXT, last_alert_at TEXT,
              kds_status INTEGER
            );
            CREATE TABLE IF NOT EXISTS runner_events(
              id INTEGER PRIMARY KEY, detail_id TEXT NOT NULL REFERENCES runner_items(detail_id),
              kind TEXT NOT NULL, created_at TEXT NOT NULL, quantity TEXT, added_quantity TEXT,
              dish_name TEXT, table_name TEXT, order_no TEXT, remaining_text TEXT
            );
            CREATE TABLE IF NOT EXISTS runner_monitor_state(
              id INTEGER PRIMARY KEY CHECK(id=1), last_success_at TEXT,
              last_error TEXT, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cukcuk_invoices(
              ref_id TEXT PRIMARY KEY, ref_no TEXT NOT NULL, ref_date TEXT NOT NULL,
              branch_id TEXT NOT NULL, payment_status INTEGER NOT NULL,
              table_name TEXT NOT NULL DEFAULT '',
              total_amount TEXT NOT NULL, cash_amount TEXT NOT NULL,
              card_amount TEXT NOT NULL, modified_date TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cukcuk_invoice_items(
              detail_id TEXT PRIMARY KEY, ref_id TEXT NOT NULL REFERENCES cukcuk_invoices(ref_id),
              item_code TEXT NOT NULL, item_name TEXT NOT NULL,
              quantity TEXT NOT NULL, amount TEXT NOT NULL, unit_name TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_cukcuk_items_code ON cukcuk_invoice_items(item_code);
            CREATE TABLE IF NOT EXISTS cukcuk_invoice_payments(
              payment_id TEXT PRIMARY KEY, ref_id TEXT NOT NULL REFERENCES cukcuk_invoices(ref_id),
              payment_type INTEGER NOT NULL, amount TEXT NOT NULL
            );
            """
        )
        init_zone_db(con)
        init_zone_shift_db(con)
        columns = {row["name"] for row in con.execute("PRAGMA table_info(users)")}
        if "department" not in columns:
            con.execute("ALTER TABLE users ADD COLUMN department TEXT NOT NULL DEFAULT 'other'")
        item_columns = {row["name"] for row in con.execute("PRAGMA table_info(items)")}
        if "units_per_carton" not in item_columns:
            con.execute("ALTER TABLE items ADD COLUMN units_per_carton INTEGER")
        con.execute("UPDATE items SET units_per_carton=12 WHERE active=1 AND group_name='liquor' AND units_per_carton IS NULL")
        con.execute("""UPDATE items SET units_per_carton=24 WHERE active=1 AND units_per_carton IS NULL
            AND group_name IN ('beer','soft_drink','water','tobacco','rice_paper','peanuts')""")
        daily_columns = {row["name"] for row in con.execute("PRAGMA table_info(daily_stock_counts)")}
        if "cartons" not in daily_columns:
            con.execute("ALTER TABLE daily_stock_counts ADD COLUMN cartons TEXT")
        if "loose_units" not in daily_columns:
            con.execute("ALTER TABLE daily_stock_counts ADD COLUMN loose_units TEXT")
        invoice_columns = {row["name"] for row in con.execute("PRAGMA table_info(cukcuk_invoices)")}
        if "table_name" not in invoice_columns:
            con.execute("ALTER TABLE cukcuk_invoices ADD COLUMN table_name TEXT NOT NULL DEFAULT ''")
        invoice_item_columns = {row["name"] for row in con.execute("PRAGMA table_info(cukcuk_invoice_items)")}
        if "unit_name" not in invoice_item_columns:
            con.execute("ALTER TABLE cukcuk_invoice_items ADD COLUMN unit_name TEXT NOT NULL DEFAULT ''")
        runner_columns = {row["name"] for row in con.execute("PRAGMA table_info(runner_items)")}
        if "source_quantity" not in runner_columns:
            con.execute("ALTER TABLE runner_items ADD COLUMN source_quantity TEXT NOT NULL DEFAULT '0'")
            con.execute("UPDATE runner_items SET source_quantity=quantity")
        if "served_quantity" not in runner_columns:
            con.execute("ALTER TABLE runner_items ADD COLUMN served_quantity TEXT NOT NULL DEFAULT '0'")
            con.execute("UPDATE runner_items SET served_quantity=CASE WHEN served_at IS NULL THEN '0' ELSE source_quantity END")
        if "kds_status" not in runner_columns:
            con.execute("ALTER TABLE runner_items ADD COLUMN kds_status INTEGER")
        if "item_key" not in runner_columns:
            con.execute("ALTER TABLE runner_items ADD COLUMN item_key TEXT")
        event_columns = {row["name"] for row in con.execute("PRAGMA table_info(runner_events)")}
        for column in ("quantity", "added_quantity", "dish_name", "table_name", "order_no", "remaining_text"):
            if column not in event_columns:
                con.execute(f"ALTER TABLE runner_events ADD COLUMN {column} TEXT")


def password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 300_000)
    return base64.b64encode(salt + digest).decode()


def password_valid(password: str, encoded: str) -> bool:
    try:
        raw = base64.b64decode(encoded)
        expected = raw[16:]
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), raw[:16], 300_000)
        return hmac.compare_digest(expected, actual)
    except (ValueError, TypeError):
        return False


def kiosk_punch(con: sqlite3.Connection, username: str, pin: str, event: str) -> dict:
    if event not in ("check-in", "check-out"):
        fail("Thao tác chấm công không hợp lệ")
    person = con.execute("SELECT id FROM users WHERE username=? AND active=1", (username,)).fetchone()
    encoded = con.execute("SELECT pin_hash FROM kiosk_pins WHERE user_id=?", (person["id"],)).fetchone() if person else None
    if not encoded or not password_valid(pin, encoded["pin_hash"]):
        fail("Sai nhân viên hoặc mã PIN", 401)
    current = now()
    if event == "check-in":
        shift = con.execute("""SELECT * FROM work_shifts WHERE user_id=? AND checked_in_at IS NULL
            AND datetime(starts_at) <= datetime(?, '+2 hours')
            AND datetime(ends_at) >= datetime(?, '-2 hours') ORDER BY starts_at LIMIT 1""",
            (person["id"], current, current)).fetchone()
        if not shift:
            fail("Không tìm thấy ca chưa chấm vào trong khung giờ")
        con.execute("UPDATE work_shifts SET checked_in_at=? WHERE id=?", (current, shift["id"]))
    else:
        shift = con.execute("""SELECT * FROM work_shifts WHERE user_id=? AND checked_in_at IS NOT NULL
            AND checked_out_at IS NULL AND datetime(ends_at) >= datetime(?, '-4 hours')
            ORDER BY starts_at DESC LIMIT 1""", (person["id"], current)).fetchone()
        if not shift:
            fail("Không tìm thấy ca đã chấm vào để chấm ra")
        con.execute("UPDATE work_shifts SET checked_out_at=? WHERE id=?", (current, shift["id"]))
    audit(con, person["id"], "kiosk-" + event, "work_shifts", shift["id"])
    return {"ok": True, "shift_id": shift["id"], "at": current}


def money(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("Số tiền không hợp lệ")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("Số tiền không hợp lệ")
    if not d.is_finite() or d != d.to_integral_value() or abs(d) > MONEY_LIMIT:
        raise ValueError("Số tiền phải là số nguyên VND")
    return int(d)


def quantity(value: object, positive: bool = False) -> Decimal:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("Số lượng không hợp lệ")
    if not d.is_finite() or abs(d) > 10**9 or d.as_tuple().exponent < -3:
        raise ValueError("Số lượng không hợp lệ (tối đa 3 chữ số thập phân)")
    if (positive and d <= 0) or (not positive and d < 0):
        raise ValueError("Số lượng phải không âm")
    return d


def clean(value: object, limit: int = 200, required: bool = True) -> str:
    result = str(value or "").strip()
    if len(result) > limit or (required and not result):
        raise ValueError("Thiếu hoặc quá dài một trường bắt buộc")
    return result


def iso_time(value: object) -> str:
    text = clean(value, 40)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.astimezone()
        return parsed.isoformat()
    except ValueError:
        raise ValueError("Ngày giờ không hợp lệ")


def audit(con: sqlite3.Connection, actor: int, action: str, entity: str, entity_id: int, detail: str = "") -> None:
    con.execute(
        "INSERT INTO audit_log(actor_id,action,entity,entity_id,detail,created_at) VALUES(?,?,?,?,?,?)",
        (actor, action, entity, entity_id, detail[:500], now()),
    )


def rowdict(row: sqlite3.Row) -> dict:
    return dict(row)


def balance(con: sqlite3.Connection, item_id: int) -> Decimal:
    moves = con.execute("SELECT quantity FROM stock_moves WHERE item_id=?", (item_id,))
    return sum((Decimal(row["quantity"]) for row in moves), Decimal(0))


def stock_list(con: sqlite3.Connection) -> list[dict]:
    result = []
    for row in con.execute("SELECT * FROM items WHERE active=1 ORDER BY group_name,name"):
        item = rowdict(row)
        item["balance"] = str(balance(con, row["id"]))
        item["low"] = Decimal(item["balance"]) < Decimal(item["min_stock"])
        totals = {"sale": Decimal(0), "waste": Decimal(0), "gift": Decimal(0), "count_adjustment": Decimal(0)}
        for move in con.execute("SELECT kind,quantity FROM stock_moves WHERE item_id=?", (row["id"],)):
            if move["kind"] in totals:
                totals[move["kind"]] += Decimal(move["quantity"])
        item["sold"] = str(-totals["sale"])
        item["waste"] = str(-totals["waste"])
        item["gift"] = str(-totals["gift"])
        item["count_adjustment"] = str(totals["count_adjustment"])
        result.append(item)
    return result


def cukcuk_summary(con: sqlite3.Connection, start: str, end: str) -> dict:
    first, last = datetime.fromisoformat(start).date(), datetime.fromisoformat(end).date()
    coverage = all(con.execute("""SELECT 1 FROM cukcuk_sync_runs WHERE from_date<=? AND to_date>=? LIMIT 1""",
        ((first+timedelta(days=step)).isoformat(), (first+timedelta(days=step)).isoformat())).fetchone()
        for step in range((last-first).days+1))
    paid = con.execute("""SELECT ref_id,ref_date,total_amount,cash_amount,card_amount
        FROM cukcuk_invoices WHERE payment_status=3 AND substr(ref_date,1,10) BETWEEN ? AND ?""",
        (start, end)).fetchall()
    totals = {"invoices": len(paid), "gross": Decimal(0), "cash": Decimal(0),
              "card": Decimal(0), "other": Decimal(0)}
    by_day: dict[str, dict] = {}
    by_month: dict[str, dict] = {}
    by_weekday: dict[int, dict] = {}
    for row in paid:
        day = row["ref_date"][:10]
        entry = by_day.setdefault(day, {"date": day, "invoices": 0, "total": Decimal(0)})
        entry["invoices"] += 1
        entry["total"] += Decimal(row["total_amount"])
        month = day[:7]
        month_entry = by_month.setdefault(month, {"month": month, "invoices": 0, "total": Decimal(0)})
        month_entry["invoices"] += 1
        month_entry["total"] += Decimal(row["total_amount"])
        weekday = datetime.fromisoformat(day).weekday()
        weekday_entry = by_weekday.setdefault(weekday, {"weekday": weekday, "invoices": 0, "total": Decimal(0)})
        weekday_entry["invoices"] += 1
        weekday_entry["total"] += Decimal(row["total_amount"])
        totals["gross"] += Decimal(row["total_amount"])
        totals["cash"] += Decimal(row["cash_amount"])
        totals["card"] += Decimal(row["card_amount"])
    totals["other"] = totals["gross"] - totals["cash"] - totals["card"]
    sales: dict[str, dict] = {}
    month_items: dict[tuple[str,str], Decimal] = {}
    for row in con.execute("""SELECT d.ref_id,d.item_code,d.item_name,d.quantity,d.amount,i.ref_date
        FROM cukcuk_invoice_items d JOIN cukcuk_invoices i ON i.ref_id=d.ref_id
        WHERE i.payment_status=3 AND substr(i.ref_date,1,10) BETWEEN ? AND ?""", (start, end)):
        code = row["item_code"] or "(không mã) " + row["item_name"]
        entry = sales.setdefault(code, {"code": code, "name": row["item_name"],
                                        "quantity": Decimal(0), "amount": Decimal(0)})
        entry["quantity"] += Decimal(row["quantity"])
        entry["amount"] += Decimal(row["amount"])
        key = (row["ref_date"][:7], code)
        month_items[key] = month_items.get(key, Decimal(0)) + Decimal(row["quantity"])
    mapped = {r["code"].upper(): dict(r) for r in con.execute(
        "SELECT code,name,group_name,unit FROM items WHERE active=1")}
    product_rows = []
    for code, row in sales.items():
        item = mapped.get(code)
        product_rows.append({**row, "group": item["group_name"] if item else "unmapped",
                             "unit": item["unit"] if item else "", "mapped": bool(item)})
    product_rows.sort(key=lambda row: (-row["quantity"], row["code"]))
    def serial(row):
        return {key: str(value) if isinstance(value, Decimal) else value for key, value in row.items()}
    return {"period": {"from": start, "to": end}, "synced": coverage, "totals": serial(totals),
            "days": [serial(row) for row in sorted(by_day.values(), key=lambda r: r["date"])],
            "months": [serial(row) for row in sorted(by_month.values(), key=lambda r: r["month"])],
            "weekdays": [serial(row) for row in sorted(by_weekday.values(), key=lambda r: r["weekday"])],
            "monthly_items": [{"month": month, "code": code, "name": sales[code]["name"], "quantity": str(q)}
                              for (month, code), q in sorted(month_items.items(), key=lambda pair: (pair[0][0], -pair[1], pair[0][1]))],
            "products": [serial(row) for row in product_rows],
            "beer_tobacco": [serial(row) for row in product_rows if row["group"] in TRACKED_GROUPS],
            "unmapped": sum(not row["mapped"] for row in product_rows)}


def daily_stock_report(con: sqlite3.Connection, day: str) -> list[dict]:
    cutoff = int(os.environ.get("BUSINESS_DAY_CUTOFF_HOUR", "5"))
    if not 0 <= cutoff <= 12:
        raise ValueError("BUSINESS_DAY_CUTOFF_HOUR phải từ 0 đến 12")
    local_zone = timezone(timedelta(hours=7))
    next_day = (datetime.fromisoformat(day).date()+timedelta(days=1)).isoformat()
    coverage = all(con.execute("""SELECT 1 FROM cukcuk_sync_runs
        WHERE from_date<=? AND to_date>=? LIMIT 1""", (target, target)).fetchone()
        for target in (day, next_day))
    sold_by_code: dict[str, Decimal] = {}
    saleable_catalog = {row["code"].upper(): dict(row) for row in con.execute(
        "SELECT code,group_name,unit,units_per_carton FROM items WHERE active=1")
        if row["group_name"] in TRACKED_GROUPS}
    unknown_sold_units = set()
    for row in con.execute("""SELECT i.ref_date,d.item_code,d.quantity,d.unit_name FROM cukcuk_invoice_items d
        JOIN cukcuk_invoices i ON i.ref_id=d.ref_id WHERE i.payment_status=3
        AND substr(i.ref_date,1,10) BETWEEN ? AND ?""", (day, next_day)):
        moment = datetime.fromisoformat(row["ref_date"])
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=local_zone)
        business_day = (moment.astimezone(local_zone)-timedelta(hours=cutoff)).date().isoformat()
        if business_day == day:
            code = canonical_code(row["item_code"])
            item = saleable_catalog.get(code)
            if item:
                try:
                    amount = converted_quantity({"Quantity": row["quantity"], "UnitName": row["unit_name"],
                                                 "ItemCode": row["item_code"]}, item)
                except ValueError:
                    amount = None
                if amount is None:
                    unknown_sold_units.add(code)
                    continue
            else:
                amount = Decimal(row["quantity"])
            sold_by_code[code] = sold_by_code.get(code, Decimal(0)) + amount
    recipe_usage: dict[int, Decimal] = {}
    recipe_items: set[int] = set()
    for recipe in con.execute("SELECT item_code,ingredient_id,quantity_per_unit FROM recipes"):
        ingredient_id = recipe["ingredient_id"]
        recipe_items.add(ingredient_id)
        recipe_usage[ingredient_id] = recipe_usage.get(ingredient_id, Decimal(0)) + (
            sold_by_code.get(recipe["item_code"], Decimal(0)) * Decimal(recipe["quantity_per_unit"]))
    result = []
    for item in con.execute("SELECT * FROM items WHERE active=1 ORDER BY group_name,code"):
        counts = {row["phase"]: Decimal(row["quantity"]) for row in con.execute(
            "SELECT phase,quantity FROM daily_stock_counts WHERE day=? AND item_id=?", (day, item["id"]))}
        previous_day = (datetime.fromisoformat(day).date() - timedelta(days=1)).isoformat()
        previous_row = con.execute("SELECT quantity FROM daily_stock_counts WHERE day=? AND phase='closing' AND item_id=?",
                                   (previous_day, item["id"])).fetchone()
        override_row = con.execute("SELECT quantity FROM daily_stock_opening_overrides WHERE day=? AND item_id=?",
                                   (day, item["id"])).fetchone()
        if override_row is not None:
            previous_row = override_row
        moves = {"receipt": Decimal(0), "return": Decimal(0), "waste": Decimal(0), "gift": Decimal(0)}
        offset = f"{7-cutoff:+d} hours"
        for move in con.execute("""SELECT kind,quantity FROM stock_moves
            WHERE item_id=? AND date(created_at,?)=?""", (item["id"], offset, day)):
            if move["kind"] in moves:
                moves[move["kind"]] += Decimal(move["quantity"])
        direct = sold_by_code.get(item["code"].upper(), Decimal(0)) if item["group_name"] in TRACKED_GROUPS else Decimal(0)
        consumed = direct + recipe_usage.get(item["id"], Decimal(0))
        opening, closing = counts.get("opening"), counts.get("closing")
        incoming_cartons_units = Decimal(0)
        if item["group_name"] in TRACKED_GROUPS:
            incoming_cartons_units = opening or Decimal(0)
            opening = Decimal(previous_row["quantity"]) if previous_row else Decimal(0)
        known_usage = item["group_name"] in TRACKED_GROUPS or item["id"] in recipe_items
        manual_moves = sum(moves.values(), Decimal(0))
        if item["group_name"] in TRACKED_GROUPS:
            manual_moves -= moves["receipt"]
        count_ready = item["group_name"] not in TRACKED_GROUPS or counts.get("opening") is not None
        saleable_unit_known = item["code"].upper() not in unknown_sold_units
        expected = opening + incoming_cartons_units + manual_moves - consumed if opening is not None and count_ready and known_usage and coverage and saleable_unit_known else None
        variance = closing - expected if closing is not None and expected is not None else None
        known_damage = -moves["waste"]
        shortage = max(Decimal(0), -variance) if variance is not None else None
        result.append({"id": item["id"], "code": item["code"], "name": item["name"], "group": item["group_name"], "unit": item["unit"],
                       "opening": str(opening) if opening is not None else None,
                        "incoming": str(incoming_cartons_units) if count_ready else None,
                        "received": str(incoming_cartons_units + (Decimal(0) if item["group_name"] in TRACKED_GROUPS else moves["receipt"]) + moves["return"]),
                       "waste_gift": str(-(moves["waste"] + moves["gift"])),
                        "sold": str(direct) if saleable_unit_known else None,
                        "unit_unknown": not saleable_unit_known,
                        "recipe_used": str(recipe_usage.get(item["id"], Decimal(0))),
                       "recipe_defined": item["id"] in recipe_items, "synced": coverage,
                       "expected": str(expected) if expected is not None else None,
                       "closing": str(closing) if closing is not None else None,
                       "variance": str(variance) if variance is not None else None,
                       "known_damage": str(known_damage),
                       "shortage_or_damage": str(shortage + known_damage) if shortage is not None else None,
                       "has_previous_closing": previous_row is not None})
    return result


def valid_shift_day(raw: str) -> str:
    try:
        parsed = datetime.fromisoformat(raw).date().isoformat()
    except (TypeError, ValueError):
        raise ValueError("Ngày phải theo dạng YYYY-MM-DD")
    if parsed != raw:
        raise ValueError("Ngày phải theo dạng YYYY-MM-DD")
    return parsed


def saved_zone_shift_report(con: sqlite3.Connection, day: str) -> dict:
    row = con.execute("SELECT * FROM zone_shift_reports WHERE day=? ORDER BY id DESC LIMIT 1", (day,)).fetchone()
    report = json.loads(row["report_json"]) if row else None
    notes = {note["invoice_id"]: note["note"] for note in con.execute(
        "SELECT invoice_id,note FROM zone_shift_notes WHERE report_id=?", (row["id"] if row else -1,))}
    allocations = [rowdict(a) for a in con.execute(
        "SELECT day,zone_id,item_code,issued,returned,ending FROM zone_tobacco_allocations WHERE day=? ORDER BY zone_id,item_code", (day,))]
    if report:
        report["id"] = row["id"]
        report["generated_at"] = row["generated_at"]
        for warning in report["warnings"]:
            warning["note"] = notes.get(warning["invoice_id"], "")
        for invoice in report.get("closed_invoices", []):
            invoice["note"] = notes.get(invoice["invoice_id"], "")
        ordered = {(zone["zone_id"], item["code"]): item["quantity"]
                   for zone in report["zones"] for item in zone["items"] if item["group"] == "tobacco"}
        for zone in report["zones"]:
            zone["tobacco_balance"] = []
            for code in ("TNN", "TM"):
                allocation = next((a for a in allocations if a["zone_id"] == zone["zone_id"] and a["item_code"] == code), None)
                issued = allocation["issued"] if allocation else None
                returned = allocation["returned"] if allocation else None
                ending = allocation["ending"] if allocation else None
                zone["tobacco_balance"].append({"code": code, "issued": issued, "returned": returned,
                    "ending": ending, "ordered": ordered.get((zone["zone_id"], code), "0"),
                    "difference": tobacco_balance(issued, returned, ending, ordered.get((zone["zone_id"], code), "0"))})
    return {"day": day, "report": report, "allocations": allocations}


def item_table_usage(con: sqlite3.Connection, day: str) -> dict:
    """Paid invoice quantities by item and table; cancellation history is unavailable."""
    cutoff = int(os.environ.get("BUSINESS_DAY_CUTOFF_HOUR", "5"))
    if not 0 <= cutoff <= 12:
        raise ValueError("BUSINESS_DAY_CUTOFF_HOUR phải từ 0 đến 12")
    local_zone = timezone(timedelta(hours=7))
    next_day = (datetime.fromisoformat(day).date() + timedelta(days=1)).isoformat()
    coverage = all(con.execute("""SELECT 1 FROM cukcuk_sync_runs
        WHERE from_date<=? AND to_date>=? LIMIT 1""", (target, target)).fetchone()
        for target in (day, next_day))
    mapped = {row["code"].upper(): row for row in con.execute(
        "SELECT code,name,group_name,unit FROM items WHERE active=1") if row["group_name"] in TRACKED_GROUPS}
    totals = {}
    for row in con.execute("""SELECT i.ref_date,i.table_name,d.item_code,d.quantity
        FROM cukcuk_invoice_items d JOIN cukcuk_invoices i ON i.ref_id=d.ref_id
        WHERE i.payment_status=3 AND substr(i.ref_date,1,10) BETWEEN ? AND ?""", (day, next_day)):
        moment = datetime.fromisoformat(row["ref_date"])
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=local_zone)
        if (moment.astimezone(local_zone) - timedelta(hours=cutoff)).date().isoformat() != day:
            continue
        code = canonical_code(row["item_code"])
        item = mapped.get(code)
        if not item:
            continue
        table_name = row["table_name"] or "Chưa có tên bàn"
        key = (code, table_name)
        totals[key] = totals.get(key, Decimal(0)) + Decimal(row["quantity"])
    by_item = {}
    for (code, table_name), amount in sorted(totals.items()):
        item = mapped[code]
        entry = by_item.setdefault(code, {"code": code, "name": item["name"],
                                         "group": item["group_name"], "unit": item["unit"],
                                         "billed_quantity": Decimal(0), "tables": []})
        entry["billed_quantity"] += amount
        entry["tables"].append({"table": table_name, "billed_quantity": str(amount),
                                "ordered_quantity": None, "returned_quantity": None})
    items = []
    for entry in by_item.values():
        entry["billed_quantity"] = str(entry["billed_quantity"])
        entry["ordered_quantity"] = None
        entry["returned_quantity"] = None
        items.append(entry)
    items.sort(key=lambda entry: (entry["group"], entry["name"]))
    return {"day": day, "synced": coverage, "items": items,
            "return_data_available": False}


def cash_summary(con: sqlite3.Connection, shift: sqlite3.Row) -> dict:
    entries = con.execute(
        "SELECT kind,method,amount FROM cash_entries WHERE shift_id=?", (shift["id"],)
    ).fetchall()
    imported = con.execute(
        "SELECT method,amount FROM sales_imports WHERE shift_id=?", (shift["id"],)
    ).fetchall()
    sales_cash = sum(r["amount"] for r in imported if r["method"] == "cash") if imported else shift["manual_cash"]
    sales_bank = sum(r["amount"] for r in imported if r["method"] == "bank") if imported else shift["manual_bank"]
    cash_other = sum(r["amount"] * (1 if r["kind"] == "income" else -1)
                     for r in entries if r["method"] == "cash")
    bank_other = sum(r["amount"] * (1 if r["kind"] == "income" else -1)
                     for r in entries if r["method"] == "bank")
    expected_cash = shift["opening_cash"] + sales_cash + cash_other
    expected_bank = sales_bank + bank_other
    out = rowdict(shift)
    out.update(
        sales_cash=sales_cash, sales_bank=sales_bank,
        expected_cash=expected_cash, expected_bank=expected_bank,
        difference_cash=None if shift["counted_cash"] is None else shift["counted_cash"] - expected_cash,
        difference_bank=None if shift["counted_bank"] is None else shift["counted_bank"] - expected_bank,
        source="csv" if imported else "manual",
    )
    return out


def fail(message: str, status: int = 400):
    raise ApiError(message, status)


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def live_table_merchandise(con: sqlite3.Connection) -> dict:
    """Fetch a fresh CUKCUK open-table snapshot for display or spot checks."""
    from cukcuk_sync import Client, CukcukError

    current = datetime.now(timezone.utc)
    shift = con.execute("""SELECT id,label,opened_at FROM cash_shifts
        WHERE locked_at IS NULL ORDER BY id DESC LIMIT 1""").fetchone()
    with TABLE_STOCK_LOCK:
        try:
            client = Client.from_environment()
            start = current - timedelta(hours=48)
            summaries = list(client.orders_since(start))
            active = {}
            for row in summaries:
                if row.get("Type") != 1 or row.get("Status") not in ACTIVE_ORDER_STATUSES or not row.get("Id"):
                    continue
                active[str(row["Id"])] = row
            if len(active) > 200:
                fail("Quá 200 đơn đang mở; cần thu hẹp thời gian quét", 503)
            orders = [client.order_detail(order_id) for order_id in active]
            catalog = TABLE_STOCK_CACHE.get("catalog")
            catalog_at = TABLE_STOCK_CACHE.get("catalog_at")
            if not catalog or not catalog_at or (current - catalog_at).total_seconds() >= 21600:
                catalog = {str(row.get("Id") or "").lower(): str(row.get("Code") or "").upper()
                           for row in client.inventory_items() if row.get("Id") and row.get("Code")}
                TABLE_STOCK_CACHE.update({"catalog": catalog, "catalog_at": current})
        except CukcukError as exc:
            fail(str(exc), 502)
        local_items = [dict(row) for row in con.execute(
            "SELECT code,name,group_name,unit,units_per_carton FROM items WHERE active=1")]
        groups = {row["code"].upper(): row["group_name"] for row in local_items}
        pack_sizes = {row["code"].upper(): row["units_per_carton"] for row in local_items}
        base_units = {row["code"].upper(): row["unit"] for row in local_items}
        names = {row["code"].upper(): row["name"] for row in local_items}
        rows, unmapped, unknown_tables = project_table_items(
            orders, catalog, groups, pack_sizes, base_units, names)
        table_status = project_table_status(orders, rows, unknown_tables)
        result = {"rows": rows, "unmapped_item_ids": unmapped,
                  "tables": table_status,
                  "active_orders": sum(order.get("Status") in ACTIVE_ORDER_STATUSES for order in orders),
                  "shift": {"id": shift["id"], "label": shift["label"], "opened_at": shift["opened_at"]} if shift else None,
                  "as_of": current.isoformat(), "scan_start": start.isoformat(), "cached": False}
        TABLE_STOCK_CACHE.update({"at": current, "shift_id": shift["id"] if shift else None, "result": result})
        return result


class Handler(BaseHTTPRequestHandler):
    server_version = "QuanLyQuan/0.1"

    def log_message(self, format: str, *args) -> None:
        print("%s %s" % (self.address_string(), format % args))

    def send_json(self, data: object, status: int = 200, cookie: str | None = None) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, name: str, mime: str) -> None:
        data = (STATIC / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'")
        self.end_headers()
        self.wfile.write(data)

    def body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 1_000_000:
                fail("Dữ liệu quá lớn", 413)
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                fail("Dữ liệu JSON phải là object")
            return data
        except (ValueError, json.JSONDecodeError):
            fail("Dữ liệu JSON không hợp lệ")

    def session(self, con: sqlite3.Connection) -> tuple[sqlite3.Row, sqlite3.Row]:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            token = cookie["session"].value
        except (KeyError, ValueError):
            fail("Vui lòng đăng nhập", 401)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        session = con.execute(
            "SELECT * FROM sessions WHERE token_hash=? AND expires_at>?",
            (token_hash, now()),
        ).fetchone()
        if not session:
            fail("Phiên đăng nhập đã hết hạn", 401)
        user = con.execute("SELECT * FROM users WHERE id=? AND active=1", (session["user_id"],)).fetchone()
        if not user:
            fail("Tài khoản đã bị khóa", 403)
        if self.command != "GET" and not hmac.compare_digest(
            self.headers.get("X-CSRF-Token", ""), session["csrf"]
        ):
            fail("Thiếu mã xác nhận phiên", 403)
        return user, session

    @staticmethod
    def require(user: sqlite3.Row, *roles: str) -> None:
        if user["role"] not in roles:
            fail("Bạn không có quyền thực hiện", 403)

    def runner_auth(self) -> None:
        key = os.environ.get("RUNNER_DEVICE_KEY", "")
        if len(key) < 32 or not hmac.compare_digest(key, self.headers.get("X-Runner-Key", "")):
            fail("Màn hình tiếp thực chưa được cấp khóa thiết bị", 403)
        origin = self.headers.get("Origin", "")
        host = self.headers.get("Host", "")
        if origin and origin not in ("http://" + host, "https://" + host):
            fail("Nguồn yêu cầu không hợp lệ", 403)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self.send_file("index.html", "text/html; charset=utf-8")
        if path == "/app.js":
            return self.send_file("app.js", "text/javascript; charset=utf-8")
        if path == "/style.css":
            return self.send_file("style.css", "text/css; charset=utf-8")
        if path == "/zone-layout.css":
            return self.send_file("zone-layout.css", "text/css; charset=utf-8")
        if path == "/kiosk":
            return self.send_file("kiosk.html", "text/html; charset=utf-8")
        if path == "/kiosk.js":
            return self.send_file("kiosk.js", "text/javascript; charset=utf-8")
        if path == "/runner":
            return self.send_file("runner.html", "text/html; charset=utf-8")
        if path == "/runner.js":
            return self.send_file("runner.js", "text/javascript; charset=utf-8")
        if path == "/runner.css":
            return self.send_file("runner.css", "text/css; charset=utf-8")
        try:
            with db() as con:
                if path == "/api/runner/queue":
                    self.runner_auth()
                    params = parse_qs(urlparse(self.path).query)
                    try:
                        after = int(params.get("after", ["-1"])[0])
                    except ValueError:
                        fail("Mã sự kiện không hợp lệ")
                    if after < -1:
                        fail("Mã sự kiện không hợp lệ")
                    items = [rowdict(row) for row in con.execute("""SELECT d.detail_id,d.item_name,d.quantity,
                        d.first_seen_at,d.last_alert_at,o.order_no,o.table_name FROM runner_items d
                        JOIN runner_orders o ON o.order_id=d.order_id
                        WHERE d.served_at IS NULL AND d.canceled_at IS NULL
                        ORDER BY d.first_seen_at,d.detail_id LIMIT 200""")]
                    latest = con.execute("SELECT COALESCE(MAX(id),0) FROM runner_events").fetchone()[0]
                    events = [] if after == -1 else [rowdict(row) for row in con.execute("""SELECT e.id,e.kind,
                        COALESCE(e.dish_name,d.item_name) AS item_name,
                        COALESCE(e.quantity,d.quantity) AS quantity,e.added_quantity,
                        COALESCE(e.order_no,o.order_no) AS order_no,
                        COALESCE(e.table_name,o.table_name) AS table_name,e.remaining_text FROM runner_events e
                        JOIN runner_items d ON d.detail_id=e.detail_id JOIN runner_orders o ON o.order_id=d.order_id
                        WHERE e.id>? ORDER BY e.id LIMIT 100""", (after,))]
                    monitor = con.execute("SELECT * FROM runner_monitor_state WHERE id=1").fetchone()
                    return self.send_json({"items": items, "events": events, "latest_event_id": latest,
                                            "monitor": rowdict(monitor) if monitor else None,
                                            "late_minutes": int(os.environ.get("RUNNER_LATE_MINUTES", "15")),
                                            "completion_mode": os.environ.get("RUNNER_COMPLETION_MODE", "runner")})
                if path == "/api/status":
                    count = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                    return self.send_json({"setup_required": count == 0})
                user, session = self.session(con)
                if path == "/api/me":
                    return self.send_json({"user": {"id": user["id"], "name": user["display_name"], "role": user["role"]}, "csrf": session["csrf"]})
                if path == "/api/cukcuk-summary":
                    self.require(user, "owner", "manager", "stock")
                    params = parse_qs(urlparse(self.path).query)
                    today = datetime.now().date()
                    start = params.get("from", [today.replace(day=1).isoformat()])[0]
                    end = params.get("to", [today.isoformat()])[0]
                    try:
                        from_day, to_day = datetime.fromisoformat(start).date(), datetime.fromisoformat(end).date()
                    except ValueError:
                        fail("Ngày phải theo dạng YYYY-MM-DD")
                    if start != from_day.isoformat() or end != to_day.isoformat() or from_day > to_day or (to_day-from_day).days > 366:
                        fail("Khoảng ngày không hợp lệ hoặc quá 366 ngày")
                    return self.send_json(cukcuk_summary(con, start, end))
                if path == "/api/table-merchandise":
                    self.require(user, "owner", "manager", "stock")
                    return self.send_json(live_table_merchandise(con))
                if path == "/api/zones":
                    self.require(user, "owner", "manager")
                    return self.send_json(config_snapshot(con))
                if path == "/api/zone-review":
                    self.require(user, "owner", "manager")
                    snapshot = config_snapshot(con)
                    report = live_table_merchandise(con)
                    pack_sizes = {row["code"].upper(): row["units_per_carton"] for row in con.execute(
                        "SELECT code,units_per_carton FROM items WHERE active=1 AND group_name IN ('beer','water','soft_drink','tobacco')")}
                    return self.send_json({"as_of": report["as_of"],
                        "tables": build_live_review(report, snapshot["zones"],
                            snapshot["tables"], snapshot["assignments"], pack_sizes),
                        "active_orders": report["active_orders"]})
                if path == "/api/zone-shift-report":
                    self.require(user, "owner", "manager")
                    raw_day = parse_qs(urlparse(self.path).query).get("day", [business_day(now())])[0]
                    return self.send_json(saved_zone_shift_report(con, valid_shift_day(raw_day)))
                if path == "/api/daily-stock-report":
                    self.require(user, "owner", "manager", "stock")
                    day = parse_qs(urlparse(self.path).query).get("day", [datetime.now(timezone(timedelta(hours=7))).date().isoformat()])[0]
                    try:
                        valid_day = datetime.fromisoformat(day).date().isoformat()
                    except ValueError:
                        fail("Ngày phải theo dạng YYYY-MM-DD")
                    if day != valid_day:
                        fail("Ngày phải theo dạng YYYY-MM-DD")
                    return self.send_json({"day": day, "rows": daily_stock_report(con, day)})
                if path == "/api/saleable-history":
                    self.require(user, "owner", "manager", "stock")
                    params = parse_qs(urlparse(self.path).query)
                    period = params.get("period", ["day"])[0]
                    anchor = valid_shift_day(params.get("anchor", [business_day(now())])[0])
                    cutoff = int(os.environ.get("BUSINESS_DAY_CUTOFF_HOUR", "5"))
                    if not 0 <= cutoff <= 12:
                        fail("Giờ cắt ngày kinh doanh không hợp lệ")
                    return self.send_json(history_report(con, period, anchor, daily_stock_report, cutoff))
                if path == "/api/daily-stock-batch":
                    self.require(user, "owner", "manager", "stock")
                    params = parse_qs(urlparse(self.path).query)
                    day = params.get("day", [""])[0]
                    phase = params.get("phase", [""])[0]
                    try:
                        parsed = datetime.fromisoformat(day).date().isoformat()
                    except ValueError:
                        fail("Ngày phải theo dạng YYYY-MM-DD")
                    if day != parsed or phase not in ("opening", "closing"):
                        fail("Ngày hoặc mốc kiểm không hợp lệ")
                    today = datetime.now(timezone(timedelta(hours=7))).date().isoformat()
                    if day != today:
                        fail("Chỉ được kiểm hàng cho ngày hiện tại")
                    previous_day = (datetime.fromisoformat(day).date() - timedelta(days=1)).isoformat()
                    items = [rowdict(row) for row in con.execute("""SELECT i.id,i.code,i.name,i.group_name,i.unit,
                        i.units_per_carton,c.quantity,c.cartons,c.loose_units,
                        COALESCE((SELECT o.quantity FROM daily_stock_opening_overrides o WHERE o.day=? AND o.item_id=i.id),
                          (SELECT p.quantity FROM daily_stock_counts p WHERE p.day=? AND p.phase='closing' AND p.item_id=i.id)) previous_closing
                        FROM items i LEFT JOIN daily_stock_counts c ON c.item_id=i.id AND c.day=? AND c.phase=?
                        WHERE i.active=1 AND i.group_name IN ('beer','liquor','soft_drink','water','tobacco','rice_paper','peanuts')
                         ORDER BY i.group_name,i.name""", (day, previous_day, day, phase))]
                    return self.send_json({"day": day, "phase": phase, "items": items,
                                           "complete": bool(items) and all(row["cartons"] is not None for row in items),
                                           "legacy_count": any(row["quantity"] is not None and row["cartons"] is None for row in items)})
                if path == "/api/item-table-usage":
                    self.require(user, "owner", "manager", "stock")
                    day = parse_qs(urlparse(self.path).query).get("day", [""])[0]
                    try:
                        parsed = datetime.fromisoformat(day).date().isoformat()
                    except ValueError:
                        fail("Ngày phải theo dạng YYYY-MM-DD")
                    if day != parsed:
                        fail("Ngày phải theo dạng YYYY-MM-DD")
                    return self.send_json(item_table_usage(con, day))
                if path == "/api/daily-usage":
                    self.require(user, "owner", "manager", "stock")
                    params = parse_qs(urlparse(self.path).query)
                    start = params.get("from", [(datetime.now(timezone(timedelta(hours=7))) - timedelta(days=29)).date().isoformat()])[0]
                    end = params.get("to", [datetime.now(timezone(timedelta(hours=7))).date().isoformat()])[0]
                    try:
                        first, last = datetime.fromisoformat(start).date(), datetime.fromisoformat(end).date()
                    except ValueError:
                        fail("Ngày phải theo dạng YYYY-MM-DD")
                    if start != first.isoformat() or end != last.isoformat() or first > last or (last-first).days > 90:
                        fail("Khoảng ngày không hợp lệ hoặc quá 90 ngày")
                    rows = [rowdict(row) for row in con.execute("""SELECT u.day,i.code,i.name,i.group_name,i.unit,u.quantity,u.note
                        FROM daily_usage u JOIN items i ON i.id=u.item_id WHERE u.day BETWEEN ? AND ?
                        ORDER BY u.day DESC,i.name""", (start, end))]
                    return self.send_json({"rows": rows, "from": start, "to": end})
                if path == "/api/dashboard":
                    if user["role"] == "staff":
                        shifts = [rowdict(r) for r in con.execute("SELECT * FROM work_shifts WHERE user_id=? ORDER BY starts_at DESC LIMIT 30", (user["id"],))]
                        return self.send_json({"work_shifts": shifts})
                    cash = [] if user["role"] == "stock" else [
                        cash_summary(con, r) for r in con.execute(
                            "SELECT * FROM cash_shifts WHERE ? != 'cashier' OR opened_by=? ORDER BY id DESC LIMIT 30",
                            (user["role"], user["id"]),
                        )
                    ]
                    counts = [rowdict(r) for r in con.execute(
                        "SELECT c.*,i.code,i.name FROM stock_counts c JOIN items i ON i.id=c.item_id ORDER BY c.id DESC LIMIT 30"
                    )]
                    items = stock_list(con)
                    work_filter = "" if user["role"] in ("owner", "manager") else "WHERE w.user_id=" + str(user["id"])
                    work = [rowdict(r) for r in con.execute(
                        "SELECT w.*,u.display_name FROM work_shifts w JOIN users u ON u.id=w.user_id " + work_filter + " ORDER BY w.starts_at DESC LIMIT 50"
                    )]
                    incidents = [rowdict(r) for r in con.execute("SELECT * FROM order_incidents ORDER BY id DESC LIMIT 30")]
                    users = [dict(id=r["id"], username=r["username"], name=r["display_name"],
                                  role=r["role"], department=r["department"])
                             for r in con.execute("SELECT * FROM users WHERE active=1 ORDER BY display_name")]
                    staff_metrics = []
                    if user["role"] in ("owner", "manager"):
                        for person in users:
                            person_shifts = con.execute(
                                "SELECT starts_at,checked_in_at FROM work_shifts WHERE user_id=?", (person["id"],)
                            ).fetchall()
                            attended = [s for s in person_shifts if s["checked_in_at"]]
                            late = sum(
                                datetime.fromisoformat(s["checked_in_at"]) >
                                datetime.fromisoformat(s["starts_at"]) + timedelta(minutes=5)
                                for s in attended
                            )
                            issues = con.execute(
                                "SELECT COUNT(*) FROM order_incidents WHERE user_id=? AND status='open'",
                                (person["id"],)
                            ).fetchone()[0]
                            staff_metrics.append({
                                "name": person["name"], "department": person["department"],
                                "scheduled": len(person_shifts),
                                "attended": len(attended), "late": late, "open_incidents": issues,
                            })
                    entries = [] if user["role"] == "stock" else [
                        rowdict(r) for r in con.execute(
                            "SELECT e.* FROM cash_entries e JOIN cash_shifts s ON s.id=e.shift_id "
                            "WHERE ? != 'cashier' OR s.opened_by=? ORDER BY e.id DESC LIMIT 50",
                            (user["role"], user["id"]),
                        )
                    ]
                    audit_rows = []
                    if user["role"] in ("owner", "manager"):
                        audit_rows = [rowdict(r) for r in con.execute(
                            "SELECT a.*,u.display_name AS actor_name FROM audit_log a "
                            "LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 100"
                        )]
                    return self.send_json({"cash_shifts": cash, "counts": counts, "items": items,
                                           "work_shifts": work, "incidents": incidents, "users": users,
                                           "entries": entries, "staff_metrics": staff_metrics,
                                           "audit": audit_rows})
                if path == "/api/report.csv":
                    self.require(user, "owner", "manager")
                    rows = [cash_summary(con, r) for r in con.execute("SELECT * FROM cash_shifts ORDER BY id")]
                    output = io.StringIO()
                    writer = csv.writer(output)
                    fields = ["id", "label", "opened_at", "sales_cash", "sales_bank", "expected_cash",
                              "expected_bank", "counted_cash", "counted_bank", "difference_cash",
                              "difference_bank", "locked_at"]
                    writer.writerow(fields)
                    for row in rows:
                        writer.writerow([row.get(k) for k in fields])
                    body = ("\ufeff" + output.getvalue()).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=bao-cao-ca.csv")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    return self.wfile.write(body)
                if path == "/api/stock-report.csv":
                    self.require(user, "owner", "manager", "stock")
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(["code", "name", "group", "unit", "balance", "sold", "waste", "gift", "count_adjustment", "min_stock", "low"])
                    for item in stock_list(con):
                        writer.writerow([item["code"], item["name"], item["group_name"],
                                         item["unit"], item["balance"], item["sold"], item["waste"],
                                         item["gift"], item["count_adjustment"], item["min_stock"], item["low"]])
                    body = ("\ufeff" + output.getvalue()).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=ton-kho.csv")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    return self.wfile.write(body)
                fail("Không tìm thấy", 404)
        except ApiError as e:
            self.send_json({"error": str(e)}, e.status)
        except Exception:
            self.send_json({"error": "Lỗi máy chủ"}, 500)
            raise

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            data = self.body()
            with db() as con:
                if path == "/api/runner/serve":
                    self.runner_auth()
                    if os.environ.get("RUNNER_COMPLETION_MODE", "runner") == "kds":
                        fail("Chế độ KDS chỉ ghi nhận hoàn thành từ CUKCUK", 409)
                    detail_id = clean(data.get("detail_id"), 80)
                    changed = con.execute("""UPDATE runner_items SET served_at=?,served_quantity=source_quantity WHERE detail_id=?
                        AND served_at IS NULL AND canceled_at IS NULL""", (now(), detail_id)).rowcount
                    if not changed:
                        fail("Món không còn trong danh sách chờ", 409)
                    audit(con, None, "runner-served", "runner_items", None, detail_id)
                    con.commit()
                    return self.send_json({"ok": True})
                if path == "/api/kiosk/punch":
                    device_key = os.environ.get("KIOSK_DEVICE_KEY", "")
                    provided = self.headers.get("X-Kiosk-Key", "")
                    if len(device_key) < 32 or not hmac.compare_digest(device_key, provided):
                        fail("Máy chấm công chưa được cấp khóa thiết bị", 403)
                    origin = self.headers.get("Origin", "")
                    if origin and origin != "http://" + self.headers.get("Host", "") and origin != "https://" + self.headers.get("Host", ""):
                        fail("Nguồn yêu cầu không hợp lệ", 403)
                    address = self.client_address[0]
                    recent = [t for t in KIOSK_ATTEMPTS.get(address, []) if (datetime.now(timezone.utc)-t).total_seconds() < 300]
                    if len(recent) >= 10:
                        fail("Thử quá nhiều lần; đợi 5 phút", 429)
                    recent.append(datetime.now(timezone.utc))
                    KIOSK_ATTEMPTS[address] = recent
                    result = kiosk_punch(con, clean(data.get("username"), 60).lower(),
                                         clean(data.get("pin"), 12), clean(data.get("event"), 20))
                    con.commit()
                    return self.send_json(result)
                if path == "/api/setup":
                    if con.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
                        fail("Đã thiết lập", 409)
                    name = clean(data.get("name"), 80)
                    password = clean(data.get("password"), 200)
                    if len(password) < 12:
                        fail("Mật khẩu cần ít nhất 12 ký tự")
                    con.execute("INSERT INTO users(username,display_name,role,department,password_hash) VALUES(?,?,?,?,?)",
                                ("owner", name, "owner", "management", password_hash(password)))
                    audit(con, 1, "setup", "users", 1)
                    con.commit()
                    return self.send_json({"ok": True}, 201)
                if path == "/api/login":
                    username = clean(data.get("username"), 60).lower()
                    password = clean(data.get("password"), 200)
                    row = con.execute("SELECT * FROM users WHERE username=? AND active=1", (username,)).fetchone()
                    if not row or not password_valid(password, row["password_hash"]):
                        fail("Sai tài khoản hoặc mật khẩu", 401)
                    token = secrets.token_urlsafe(32)
                    csrf = secrets.token_urlsafe(24)
                    expires = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
                    con.execute("INSERT INTO sessions VALUES(?,?,?,?)",
                                (hashlib.sha256(token.encode()).hexdigest(), row["id"], csrf, expires))
                    con.commit()
                    secure = "; Secure" if self.headers.get("X-Forwarded-Proto") == "https" else ""
                    cookie = f"session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200{secure}"
                    return self.send_json({"ok": True}, cookie=cookie)
                user, session = self.session(con)
                if path == "/api/logout":
                    con.execute("DELETE FROM sessions WHERE token_hash=?", (session["token_hash"],))
                    con.commit()
                    return self.send_json({"ok": True}, cookie="session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")
                result = self.mutate(con, user, path, data)
                con.commit()
                self.send_json(result, 201)
        except ApiError as e:
            self.send_json({"error": str(e)}, e.status)
        except (ValueError, sqlite3.IntegrityError) as e:
            self.send_json({"error": str(e)}, 400)
        except Exception:
            self.send_json({"error": "Lỗi máy chủ"}, 500)
            raise

    def mutate(self, con: sqlite3.Connection, user: sqlite3.Row, path: str, data: dict) -> dict:
        uid = user["id"]
        if path == "/api/zone-shift-report":
            self.require(user, "owner", "manager")
            day = valid_shift_day(data.get("day"))
            if day > business_day(now()):
                fail("Không thể tính cho ngày tương lai")
            from cukcuk_sync import Client, CukcukError
            try:
                client = Client.from_environment()
                if day == business_day(now()):
                    active = [row for row in client.orders_since(datetime.now(timezone.utc)-timedelta(hours=48))
                              if row.get("Type") == 1 and row.get("Status") in ACTIVE_ORDER_STATUSES]
                    if active:
                        fail("Còn bàn đang mở trên CUKCUK; hãy đóng hết bàn rồi tính báo cáo", 409)
                invoices = list(client.invoices(datetime.fromisoformat(day).date(),
                                                datetime.fromisoformat(day).date()+timedelta(days=1)))
            except CukcukError as exc:
                fail(str(exc), 502)
            if len(invoices) > 10000:
                fail("Quá nhiều hóa đơn trong một ngày; không tạo báo cáo", 503)
            config = config_snapshot(con)
            items = [dict(row) for row in con.execute(
                "SELECT code,name,group_name,unit,units_per_carton FROM items WHERE active=1")]
            cutoff = int(os.environ.get("BUSINESS_DAY_CUTOFF_HOUR", "5"))
            report = project_invoices(invoices, day, config["zones"], config["tables"], items, cutoff)
            report["stock"] = reconcile_stock(daily_stock_report(con, day), report["sold"],
                set(report["unknown_units"]), bool(report["unmapped_codes"]))
            report["mapping_as_of"] = now()
            previous = con.execute("SELECT id FROM zone_shift_reports WHERE day=? ORDER BY id DESC LIMIT 1", (day,)).fetchone()
            cur = con.execute("INSERT INTO zone_shift_reports(day,generated_at,generated_by,report_json) VALUES(?,?,?,?)",
                              (day, now(), uid, json.dumps(report, ensure_ascii=False)))
            if previous:
                con.execute("""INSERT INTO zone_shift_notes(report_id,invoice_id,note,updated_at,updated_by)
                    SELECT ?,invoice_id,note,updated_at,updated_by FROM zone_shift_notes WHERE report_id=?""",
                    (cur.lastrowid, previous["id"]))
            audit(con, uid, "generate", "zone_shift_reports", cur.lastrowid)
            return saved_zone_shift_report(con, day)
        if path == "/api/zone-tobacco-allocation":
            self.require(user, "owner", "manager")
            day = valid_shift_day(data.get("day"))
            zone_id = int(data.get("zone_id", 0))
            code = str(data.get("item_code") or "").upper()
            if code not in ("TNN", "TM") or not con.execute("SELECT 1 FROM zones WHERE id=? AND active=1", (zone_id,)).fetchone():
                fail("Khu hoặc loại thuốc không hợp lệ")
            previous = con.execute(
                "SELECT issued,returned,ending FROM zone_tobacco_allocations WHERE day=? AND zone_id=? AND item_code=?",
                (day, zone_id, code)).fetchone()
            values = []
            for field in ("issued", "returned", "ending"):
                raw = data[field] if field in data else previous[field] if previous else None
                if raw is None or raw == "":
                    values.append(None)
                else:
                    amount = shift_number(raw)
                    if amount != amount.to_integral_value():
                        fail("Số gói thuốc phải là số nguyên")
                    values.append(shift_fmt(amount))
            con.execute("""INSERT INTO zone_tobacco_allocations(day,zone_id,item_code,issued,returned,ending,updated_at,updated_by)
                VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(day,zone_id,item_code) DO UPDATE SET
                issued=excluded.issued,returned=excluded.returned,ending=excluded.ending,
                updated_at=excluded.updated_at,updated_by=excluded.updated_by""",
                (day, zone_id, code, *values, now(), uid))
            audit(con, uid, "save", "zone_tobacco_allocations", zone_id, f"{day}:{code}")
            return saved_zone_shift_report(con, day)
        if path in ("/api/zone-tobacco-issue", "/api/zone-tobacco-unissue"):
            self.require(user, "owner", "manager")
            day = valid_shift_day(data.get("day"))
            if day != business_day(now()):
                fail("Chỉ ghi thuốc đã lấy cho ngày kinh doanh hiện tại")
            zone_id = int(data.get("zone_id", 0))
            code = str(data.get("item_code") or "").upper()
            if code not in ("TNN", "TM") or not con.execute(
                    "SELECT 1 FROM zones WHERE id=? AND active=1", (zone_id,)).fetchone():
                fail("Khu hoặc loại thuốc không hợp lệ")
            row = con.execute("SELECT issued FROM zone_tobacco_allocations WHERE day=? AND zone_id=? AND item_code=?",
                              (day, zone_id, code)).fetchone()
            issued = shift_number(row["issued"]) if row and row["issued"] is not None else Decimal(0)
            delta = 1 if path == "/api/zone-tobacco-issue" else -1
            if issued + delta < 0:
                fail("Số gói đã lấy không thể nhỏ hơn 0")
            con.execute("""INSERT INTO zone_tobacco_allocations(day,zone_id,item_code,issued,returned,ending,updated_at,updated_by)
                VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(day,zone_id,item_code) DO UPDATE SET
                issued=excluded.issued,updated_at=excluded.updated_at,updated_by=excluded.updated_by""",
                (day, zone_id, code, shift_fmt(issued + delta), "0", None, now(), uid))
            audit(con, uid, "issue" if delta > 0 else "correct-issue", "zone_tobacco_allocations",
                  zone_id, f"{day}:{code}:{delta:+d}")
            return saved_zone_shift_report(con, day)
        if path == "/api/zone-shift-note":
            self.require(user, "owner", "manager")
            report_id = int(data.get("report_id", 0))
            invoice_id = clean(data.get("invoice_id"), 80)
            note = clean(data.get("note"), 500, required=False)
            row = con.execute("SELECT day,report_json FROM zone_shift_reports WHERE id=?", (report_id,)).fetchone()
            if not row:
                fail("Hóa đơn không thuộc báo cáo", 404)
            report = json.loads(row["report_json"])
            allowed = {entry["invoice_id"] for entry in report.get("closed_invoices", report["warnings"])}
            if invoice_id not in allowed:
                fail("Hóa đơn không thuộc báo cáo", 404)
            con.execute("""INSERT INTO zone_shift_notes(report_id,invoice_id,note,updated_at,updated_by)
                VALUES(?,?,?,?,?) ON CONFLICT(report_id,invoice_id) DO UPDATE SET
                note=excluded.note,updated_at=excluded.updated_at,updated_by=excluded.updated_by""",
                (report_id, invoice_id, note, now(), uid))
            audit(con, uid, "note", "zone_shift_notes", report_id, invoice_id)
            return saved_zone_shift_report(con, row["day"])
        if path == "/api/zones":
            self.require(user, "owner", "manager")
            name = clean(data.get("name"), 60)
            raw_tables = data.get("tables", [])
            if not isinstance(raw_tables, list) or len(raw_tables) > 100:
                fail("Danh sách bàn không hợp lệ")
            table_names = [table_number(value) for value in raw_tables]
            if any(value is None for value in table_names) or len(table_names) != len(set(table_names)):
                fail("Số bàn không hợp lệ hoặc bị trùng")
            if table_names and con.execute("SELECT 1 FROM zone_tables WHERE table_name IN (" +
                ",".join("?" for _ in table_names) + ") LIMIT 1", table_names).fetchone():
                fail("Có bàn đã thuộc một khu khác")
            cur = con.execute("INSERT INTO zones(name,created_at,created_by) VALUES(?,?,?)",
                              (name, now(), uid))
            for table_name in table_names:
                con.execute("INSERT INTO zone_tables(table_name,zone_id,updated_at,updated_by) VALUES(?,?,?,?)",
                    (table_name, cur.lastrowid, now(), uid))
            audit(con, uid, "create", "zones", cur.lastrowid)
            return {"id": cur.lastrowid}
        if path == "/api/zones/rename":
            self.require(user, "owner", "manager")
            zone_id = int(data.get("zone_id", 0))
            name = clean(data.get("name"), 60)
            changed = con.execute("UPDATE zones SET name=? WHERE id=? AND active=1", (name, zone_id)).rowcount
            if not changed:
                fail("Khu không còn hoạt động", 404)
            audit(con, uid, "rename", "zones", zone_id)
            return {"ok": True}
        if path == "/api/zone-tables":
            self.require(user, "owner", "manager")
            table_name = table_number(clean(data.get("table_name"), 80))
            if table_name is None:
                fail("Chỉ nhập số bàn, ví dụ 101")
            zone_id = int(data.get("zone_id", 0))
            if not con.execute("SELECT 1 FROM zones WHERE id=? AND active=1", (zone_id,)).fetchone():
                fail("Khu không hợp lệ")
            old_name = data.get("old_table_name")
            if old_name:
                old_name = table_number(clean(old_name, 80))
                if old_name is None:
                    fail("Số bàn cũ không hợp lệ")
                if table_name != old_name and con.execute(
                    "SELECT 1 FROM zone_tables WHERE table_name=?", (table_name,)).fetchone():
                    fail("Bàn mới đã thuộc một khu khác")
                changed = con.execute("""UPDATE zone_tables SET table_name=?,zone_id=?,
                    updated_at=?,updated_by=? WHERE table_name=?""",
                    (table_name, zone_id, now(), uid, old_name)).rowcount
                if not changed:
                    fail("Bàn cần sửa không còn tồn tại", 404)
            else:
                if con.execute("SELECT 1 FROM zone_tables WHERE table_name=?", (table_name,)).fetchone():
                    fail("Bàn này đã thuộc một khu; hãy sửa trong thẻ khu")
                con.execute("""INSERT INTO zone_tables(table_name,zone_id,updated_at,updated_by)
                    VALUES(?,?,?,?)""", (table_name, zone_id, now(), uid))
            audit(con, uid, "assign", "zone_tables", None, table_name)
            return {"ok": True}
        if path == "/api/zone-tables/remove":
            self.require(user, "owner", "manager")
            table_name = clean(data.get("table_name"), 80)
            if not con.execute("DELETE FROM zone_tables WHERE table_name=?", (table_name,)).rowcount:
                fail("Bàn chưa được gán khu", 404)
            audit(con, uid, "remove", "zone_tables", None, table_name)
            return {"ok": True}
        if path == "/api/zone-assignments":
            self.require(user, "owner", "manager")
            zone_id = int(data.get("zone_id", 0))
            staff_id = int(data.get("user_id", 0))
            if not con.execute("SELECT 1 FROM zones WHERE id=? AND active=1", (zone_id,)).fetchone():
                fail("Khu không hợp lệ")
            if not con.execute("SELECT 1 FROM users WHERE id=? AND active=1", (staff_id,)).fetchone():
                fail("Nhân viên không hợp lệ")
            starts_at, ends_at = iso_time(data.get("starts_at")), iso_time(data.get("ends_at"))
            if datetime.fromisoformat(starts_at) >= datetime.fromisoformat(ends_at):
                fail("Giờ kết thúc phải sau giờ bắt đầu")
            cur = con.execute("""INSERT INTO zone_assignments(zone_id,user_id,starts_at,ends_at,
                created_at,created_by) VALUES(?,?,?,?,?,?)""", (zone_id, staff_id, starts_at, ends_at, now(), uid))
            audit(con, uid, "assign", "zone_assignments", cur.lastrowid)
            return {"id": cur.lastrowid}
        if path == "/api/zone-assignments/remove":
            self.require(user, "owner", "manager")
            assignment_id = int(data.get("assignment_id", 0))
            if not con.execute("UPDATE zone_assignments SET active=0 WHERE id=? AND active=1", (assignment_id,)).rowcount:
                fail("Phân công không còn hoạt động", 404)
            audit(con, uid, "remove", "zone_assignments", assignment_id)
            return {"ok": True}
        if path == "/api/zone-observations":
            self.require(user, "owner", "manager")
            table_name = clean(data.get("table_name"), 80)
            observed = data.get("observed")
            if not isinstance(observed, dict):
                fail("Hãy nhập số hàng quản lý đã kiểm tại bàn")
            report = live_table_merchandise(con)
            try:
                lines, mapping_status = compare_observation(report, table_name, observed)
            except ValueError as exc:
                fail(str(exc))
            setup = config_snapshot(con)
            zone_by_table = {table_number(row["table_name"]): row["zone_id"] for row in setup["tables"]}
            zone_id = zone_by_table.get(table_number(table_name)) if mapping_status == "mapped" else None
            assigned = staff_at(setup["assignments"], zone_id, report["as_of"])
            has_surplus = any(Decimal(line["surplus_qty"] or "0") > 0 for line in lines)
            status = "unverifiable" if mapping_status != "mapped" else "open" if has_surplus else "clear"
            cur = con.execute("""INSERT INTO zone_observations(table_name,zone_id,observed_at,observed_by,
                order_as_of,mapping_status,assigned_staff_json,status) VALUES(?,?,?,?,?,?,?,?)""",
                (table_name, zone_id, report["as_of"], uid, report["as_of"], mapping_status,
                 json.dumps(assigned, ensure_ascii=False), status))
            for line in lines:
                con.execute("""INSERT INTO zone_observation_items(observation_id,group_name,
                    observed_qty,ordered_qty,surplus_qty) VALUES(?,?,?,?,?)""",
                    (cur.lastrowid, line["group"], line["observed_qty"], line["ordered_qty"], line["surplus_qty"]))
            audit(con, uid, "observe", "zone_observations", cur.lastrowid)
            return {"id": cur.lastrowid, "status": status, "items": lines, "assigned_staff": assigned}
        if path == "/api/zone-observations/resolve":
            self.require(user, "owner", "manager")
            observation_id = int(data.get("observation_id", 0))
            status = clean(data.get("status"), 20)
            if status not in ("explained", "action_needed"):
                fail("Kết quả xác minh không hợp lệ")
            note = clean(data.get("note"), 500)
            changed = con.execute("""UPDATE zone_observations SET status=?,resolution_note=?,
                resolved_at=?,resolved_by=? WHERE id=? AND status='open'""",
                (status, note, now(), uid, observation_id)).rowcount
            if not changed:
                fail("Lần kiểm không còn chờ xác minh", 409)
            audit(con, uid, "resolve", "zone_observations", observation_id)
            return {"ok": True}
        if path == "/api/daily-stock-inline":
            self.require(user, "owner", "manager")
            day = clean(data.get("day"), 10)
            if day != datetime.now(timezone(timedelta(hours=7))).date().isoformat():
                fail("Chỉ được sửa số của ngày hiện tại")
            item_id = int(data.get("item_id", 0))
            item = con.execute("SELECT id,group_name,units_per_carton FROM items WHERE id=? AND active=1", (item_id,)).fetchone()
            if not item or item["group_name"] not in TRACKED_GROUPS:
                fail("Mặt hàng không hợp lệ")
            field = clean(data.get("field"), 30)
            amount = quantity(data.get("quantity"))
            if field == "previous_closing":
                con.execute("""INSERT INTO daily_stock_opening_overrides(day,item_id,quantity,created_at,created_by)
                    VALUES(?,?,?,?,?) ON CONFLICT(day,item_id) DO UPDATE SET
                    quantity=excluded.quantity,created_at=excluded.created_at,created_by=excluded.created_by""",
                    (day, item_id, str(amount), now(), uid))
            elif field == "incoming":
                factor = item["units_per_carton"]
                if factor is None:
                    fail("Chưa có số lon/chai mỗi thùng")
                if amount != amount.to_integral_value():
                    fail("Số lon/chai nhập phải là số nguyên")
                if amount % Decimal(factor) != 0:
                    fail("Số nhập phải chia hết cho số lon/chai mỗi thùng")
                cartons = amount / Decimal(factor)
                con.execute("""INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by,cartons)
                    VALUES(?,'opening',?,?,?,?,?) ON CONFLICT(day,phase,item_id) DO UPDATE SET
                    quantity=excluded.quantity,cartons=excluded.cartons,
                    created_at=excluded.created_at,created_by=excluded.created_by""",
                    (day, item_id, str(amount), now(), uid, str(cartons)))
            else:
                fail("Cột sửa không hợp lệ")
            audit(con, uid, "daily-stock-inline-" + field, "items", item_id, day)
            return {"ok": True, "quantity": str(amount)}
        if path == "/api/daily-stock-batch":
            self.require(user, "owner", "manager")
            day = clean(data.get("day"), 10)
            try:
                parsed = datetime.fromisoformat(day).date().isoformat()
            except ValueError:
                fail("Ngày phải theo dạng YYYY-MM-DD")
            phase = clean(data.get("phase"), 10)
            if day != parsed or phase not in ("opening", "closing"):
                fail("Ngày hoặc mốc kiểm không hợp lệ")
            if day != datetime.now(timezone(timedelta(hours=7))).date().isoformat():
                fail("Chỉ được nhập hàng và kiểm kho cho ngày hiện tại")
            submitted = data.get("items")
            if not isinstance(submitted, list) or not submitted or len(submitted) > 300:
                fail("Danh sách kiểm kê không hợp lệ")
            catalog = {row["id"]: row for row in con.execute("""SELECT id,group_name,units_per_carton FROM items WHERE active=1
                AND group_name IN ('beer','liquor','soft_drink','water','tobacco','rice_paper','peanuts')""")}
            expected = set(catalog)
            if not expected:
                fail("Chưa có mặt hàng trong nhóm kiểm kê")
            checked = {}
            for row in submitted:
                if not isinstance(row, dict):
                    fail("Dòng kiểm kê không hợp lệ")
                item_id = int(row.get("item_id", 0))
                if item_id in checked:
                    fail("Trùng mặt hàng trong lượt kiểm")
                cartons = quantity(row.get("cartons"))
                if cartons != cartons.to_integral_value():
                    fail("Số thùng/cây phải là số nguyên")
                factor = catalog.get(item_id)
                loose = quantity(row.get("loose_units", 0))
                if loose != loose.to_integral_value():
                    fail("Số đơn vị lẻ phải là số nguyên")
                if factor is None or ((cartons > 0 or loose > 0) and factor["units_per_carton"] is None):
                    fail("Mặt hàng có số lượng lớn hơn 0 cần khai báo quy cách mỗi thùng/cây")
                if factor["units_per_carton"] is not None and loose >= factor["units_per_carton"]:
                    fail("Số đơn vị lẻ phải nhỏ hơn quy cách mỗi thùng/cây")
                checked[item_id] = (cartons * (factor["units_per_carton"] or 0) + loose, cartons, loose)
            previous = {row["item_id"]: Decimal(row["quantity"]) for row in con.execute(
                "SELECT item_id,quantity FROM daily_stock_counts WHERE day=? AND phase=?", (day, phase))}
            inserted = 0
            for item_id, (amount, cartons, loose) in checked.items():
                if item_id in previous:
                    con.execute("UPDATE daily_stock_counts SET quantity=?,cartons=?,loose_units=?,created_at=?,created_by=? WHERE day=? AND phase=? AND item_id=?",
                                (str(amount), str(cartons), str(loose), now(), uid, day, phase, item_id))
                else:
                    con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by,cartons,loose_units) VALUES(?,?,?,?,?,?,?,?)",
                                (day, phase, item_id, str(amount), now(), uid, str(cartons), str(loose)))
                    inserted += 1
            audit(con, uid, "daily-count-batch-" + phase, "daily_stock_counts", None,
                  f"{day}: {len(checked)} mặt hàng, {inserted} dòng mới")
            return {"ok": True, "count": len(checked), "inserted": inserted}
        if path == "/api/daily-stock-counts":
            self.require(user, "owner", "manager", "stock")
            day = clean(data.get("day"), 10)
            try:
                parsed = datetime.fromisoformat(day).date().isoformat()
            except ValueError:
                fail("Ngày phải theo dạng YYYY-MM-DD")
            if day != parsed:
                fail("Ngày phải theo dạng YYYY-MM-DD")
            phase = clean(data.get("phase"), 10)
            if phase not in ("opening", "closing"):
                fail("Chọn đầu ca hoặc cuối ca")
            item_id = int(data.get("item_id", 0))
            item = con.execute("SELECT group_name FROM items WHERE id=? AND active=1", (item_id,)).fetchone()
            if not item:
                fail("Mặt hàng không tồn tại")
            if item["group_name"] in DAILY_USAGE_GROUPS:
                fail("Đá và than chỉ ghi lượng dùng theo ngày")
            if item["group_name"] in TRACKED_GROUPS:
                fail("Nhóm hàng bán trực tiếp phải nhập theo thùng ở màn Kiểm tra hàng")
            counted = quantity(data.get("quantity"))
            if counted < 0:
                fail("Số kiểm phải không âm")
            if con.execute("SELECT 1 FROM daily_stock_counts WHERE day=? AND phase=? AND item_id=?",
                           (day, phase, item_id)).fetchone():
                fail("Đã ghi số kiểm cho mặt hàng này; cần quản lý xác minh trước khi sửa", 409)
            con.execute("INSERT INTO daily_stock_counts(day,phase,item_id,quantity,created_at,created_by) VALUES(?,?,?,?,?,?)",
                        (day, phase, item_id, str(counted), now(), uid))
            audit(con, uid, "daily-count-" + phase, "items", item_id, day)
            return {"ok": True}
        if path == "/api/daily-usage":
            self.require(user, "owner", "manager", "stock")
            day = clean(data.get("day"), 10)
            try:
                parsed = datetime.fromisoformat(day).date().isoformat()
            except ValueError:
                fail("Ngày phải theo dạng YYYY-MM-DD")
            if day != parsed:
                fail("Ngày phải theo dạng YYYY-MM-DD")
            item_id = int(data.get("item_id", 0))
            item = con.execute("SELECT group_name FROM items WHERE id=? AND active=1", (item_id,)).fetchone()
            if not item or item["group_name"] not in DAILY_USAGE_GROUPS:
                fail("Chỉ ghi lượng dùng cho đá hoặc than")
            amount = quantity(data.get("quantity"), True)
            note = clean(data.get("note", ""), 200, False)
            if con.execute("SELECT 1 FROM daily_usage WHERE day=? AND item_id=?", (day, item_id)).fetchone():
                fail("Đã ghi lượng dùng cho ngày này; cần kiểm tra trước khi sửa", 409)
            con.execute("INSERT INTO daily_usage(day,item_id,quantity,note,created_at,created_by) VALUES(?,?,?,?,?,?)",
                        (day, item_id, str(amount), note, now(), uid))
            audit(con, uid, "daily-usage", "items", item_id, day)
            return {"ok": True}
        if path == "/api/recipes":
            self.require(user, "owner", "manager", "stock")
            code = clean(data.get("item_code"), 40).upper()
            ingredient_id = int(data.get("ingredient_id", 0))
            if not con.execute("SELECT 1 FROM items WHERE id=? AND active=1", (ingredient_id,)).fetchone():
                fail("Nguyên liệu không tồn tại")
            per_unit = quantity(data.get("quantity_per_unit"), True)
            con.execute("""INSERT INTO recipes(item_code,ingredient_id,quantity_per_unit) VALUES(?,?,?)
                ON CONFLICT(item_code,ingredient_id) DO UPDATE SET quantity_per_unit=excluded.quantity_per_unit""",
                (code, ingredient_id, str(per_unit)))
            audit(con, uid, "set-recipe", "items", ingredient_id, code)
            return {"ok": True}
        if path == "/api/kiosk/pins":
            self.require(user, "owner", "manager")
            employee_id = int(data.get("user_id", 0))
            pin = clean(data.get("pin"), 12)
            if not re.fullmatch(r"[0-9]{6,8}", pin):
                fail("PIN phải gồm 6 đến 8 chữ số")
            employee = con.execute("SELECT id FROM users WHERE id=? AND active=1", (employee_id,)).fetchone()
            if not employee:
                fail("Nhân viên không tồn tại")
            con.execute("INSERT INTO kiosk_pins(user_id,pin_hash) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET pin_hash=excluded.pin_hash",
                        (employee_id, password_hash(pin)))
            audit(con, uid, "set-kiosk-pin", "users", employee_id)
            return {"ok": True}
        if path == "/api/users":
            self.require(user, "owner", "manager")
            username = clean(data.get("username"), 60).lower()
            if not re.fullmatch(r"[a-z0-9_.-]{3,60}", username):
                fail("Tên đăng nhập chỉ gồm chữ thường, số, dấu chấm, gạch")
            role = clean(data.get("role"), 20)
            if role not in ROLES or role == "owner":
                fail("Vai trò không hợp lệ")
            if role == "manager" and user["role"] != "owner":
                fail("Chỉ chủ quán được tạo quản lý", 403)
            department = clean(data.get("department", "other"), 20)
            if department not in DEPARTMENTS:
                fail("Bộ phận không hợp lệ")
            password = clean(data.get("password"), 200)
            if len(password) < 12:
                fail("Mật khẩu cần ít nhất 12 ký tự")
            cur = con.execute("INSERT INTO users(username,display_name,role,department,password_hash) VALUES(?,?,?,?,?)",
                              (username, clean(data.get("name"), 80), role, department, password_hash(password)))
            audit(con, uid, "create", "users", cur.lastrowid)
            return {"id": cur.lastrowid}
        if path == "/api/cash-shifts":
            self.require(user, "owner", "manager", "cashier")
            opening = money(data.get("opening_cash", 0))
            if opening < 0:
                fail("Tiền đầu ca không âm")
            cur = con.execute("INSERT INTO cash_shifts(label,opened_at,opened_by,opening_cash) VALUES(?,?,?,?)",
                              (clean(data.get("label"), 80), now(), uid, opening))
            audit(con, uid, "open", "cash_shifts", cur.lastrowid)
            return {"id": cur.lastrowid}
        match = re.fullmatch(r"/api/cash-shifts/(\d+)/(update|close)", path)
        if match:
            self.require(user, "owner", "manager", "cashier")
            sid = int(match.group(1))
            shift = con.execute("SELECT * FROM cash_shifts WHERE id=?", (sid,)).fetchone()
            if not shift or shift["locked_at"]:
                fail("Ca không tồn tại hoặc đã khóa")
            if user["role"] == "cashier" and shift["opened_by"] != uid:
                fail("Thu ngân chỉ được sửa ca của mình", 403)
            if match.group(2) == "update":
                cash = money(data.get("manual_cash", 0))
                bank = money(data.get("manual_bank", 0))
                counted_cash = money(data.get("counted_cash", 0))
                counted_bank = money(data.get("counted_bank", 0))
                if min(cash, bank, counted_cash, counted_bank) < 0:
                    fail("Số tiền không âm")
                con.execute("UPDATE cash_shifts SET manual_cash=?,manual_bank=?,counted_cash=?,counted_bank=?,note=? WHERE id=?",
                            (cash, bank, counted_cash, counted_bank, clean(data.get("note", ""), 500, False), sid))
                audit(con, uid, "update", "cash_shifts", sid, json.dumps({
                    "before": {k: shift[k] for k in ("manual_cash", "manual_bank", "counted_cash", "counted_bank")},
                    "after": {"manual_cash": cash, "manual_bank": bank,
                              "counted_cash": counted_cash, "counted_bank": counted_bank},
                }, ensure_ascii=False))
                return cash_summary(con, con.execute("SELECT * FROM cash_shifts WHERE id=?", (sid,)).fetchone())
            self.require(user, "owner", "manager")
            summary = cash_summary(con, shift)
            if shift["counted_cash"] is None or shift["counted_bank"] is None:
                fail("Cần nhập tiền thực đếm trước khi khóa")
            reason = clean(data.get("reason", ""), 500, False)
            if (summary["difference_cash"] or summary["difference_bank"]) and not reason:
                fail("Ca chênh lệch cần lý do")
            con.execute("UPDATE cash_shifts SET locked_at=?,locked_by=?,note=trim(note || ' ' || ?) WHERE id=?",
                        (now(), uid, reason, sid))
            audit(con, uid, "lock", "cash_shifts", sid, reason)
            return {"id": sid}
        if path == "/api/cash-entries":
            self.require(user, "owner", "manager", "cashier")
            sid = int(data.get("shift_id", 0))
            shift = con.execute("SELECT locked_at FROM cash_shifts WHERE id=?", (sid,)).fetchone()
            if not shift or shift["locked_at"]:
                fail("Ca không tồn tại hoặc đã khóa")
            if user["role"] == "cashier":
                owner = con.execute("SELECT opened_by FROM cash_shifts WHERE id=?", (sid,)).fetchone()
                if owner["opened_by"] != uid:
                    fail("Thu ngân chỉ được ghi vào ca của mình", 403)
            kind = clean(data.get("kind"), 20)
            method = clean(data.get("method"), 20)
            if kind not in ("income", "expense", "refund") or method not in ("cash", "bank"):
                fail("Loại giao dịch không hợp lệ")
            amount = money(data.get("amount"))
            if amount <= 0:
                fail("Số tiền phải lớn hơn 0")
            cur = con.execute(
                "INSERT INTO cash_entries(shift_id,kind,amount,method,note,reference,created_at,created_by) VALUES(?,?,?,?,?,?,?,?)",
                (sid, kind, amount, method, clean(data.get("note"), 200),
                 clean(data.get("reference", ""), 100, False), now(), uid))
            audit(con, uid, "create", "cash_entries", cur.lastrowid)
            return {"id": cur.lastrowid}
        if path == "/api/items":
            self.require(user, "owner", "manager", "stock")
            code = clean(data.get("code"), 40).upper()
            if not re.fullmatch(r"[A-Z0-9_. -]+", code):
                fail("Mã hàng không hợp lệ")
            if con.execute("SELECT 1 FROM items WHERE code=?", (code,)).fetchone():
                fail("Mã CUKCUK đã có trong danh mục", 409)
            group = clean(data.get("group_name"), 20)
            if group not in ITEM_GROUPS:
                fail("Nhóm hàng không hợp lệ")
            minimum = quantity(data.get("min_stock", 0))
            if group in DAILY_USAGE_GROUPS:
                minimum = Decimal(0)
            carton_raw = data.get("units_per_carton")
            carton_size = None
            if carton_raw not in (None, ""):
                try:
                    carton_size = int(carton_raw)
                except (TypeError, ValueError):
                    fail("Quy cách mỗi thùng/cây phải là số nguyên")
                if not 1 <= carton_size <= 1000:
                    fail("Quy cách mỗi thùng/cây phải từ 1 đến 1000")
            if group == "liquor" and carton_size is None:
                carton_size = 12
            elif group == "tobacco" and carton_size is None:
                carton_size = 10
            elif group in TRACKED_GROUPS and carton_size is None:
                carton_size = 24
            cur = con.execute("INSERT INTO items(code,name,group_name,unit,min_stock,units_per_carton) VALUES(?,?,?,?,?,?)",
                    (code, clean(data.get("name"), 100), group,
                                "Chai" if group == "liquor" else clean(data.get("unit"), 30), str(minimum), carton_size))
            with TABLE_STOCK_LOCK:
                TABLE_STOCK_CACHE.pop("catalog", None)
                TABLE_STOCK_CACHE.pop("catalog_at", None)
            audit(con, uid, "create", "items", cur.lastrowid)
            return {"id": cur.lastrowid}
        carton_match = re.fullmatch(r"/api/items/(\d+)/carton-size", path)
        if carton_match:
            self.require(user, "owner", "manager")
            item_id = int(carton_match.group(1))
            units = int(data.get("units_per_carton", 0))
            if not 1 <= units <= 1000:
                fail("Quy cách mỗi thùng/cây phải từ 1 đến 1000")
            item = con.execute("SELECT id,group_name FROM items WHERE id=? AND active=1", (item_id,)).fetchone()
            if not item:
                fail("Không có mặt hàng")
            con.execute("UPDATE items SET units_per_carton=? WHERE id=?", (units, item_id))
            today = datetime.now(timezone(timedelta(hours=7))).date().isoformat()
            for saved in con.execute("SELECT phase,cartons,loose_units FROM daily_stock_counts WHERE day=? AND item_id=? AND cartons IS NOT NULL",
                                      (today, item_id)).fetchall():
                con.execute("UPDATE daily_stock_counts SET quantity=? WHERE day=? AND phase=? AND item_id=?",
                            (str(Decimal(saved["cartons"]) * units + Decimal(saved["loose_units"] or 0)), today, saved["phase"], item_id))
            audit(con, uid, "update", "items", item_id, "units_per_carton")
            return {"id": item_id, "units_per_carton": units}
        if path == "/api/stock-moves":
            self.require(user, "owner", "manager", "stock")
            item_id = int(data.get("item_id", 0))
            item = con.execute("SELECT group_name FROM items WHERE id=? AND active=1", (item_id,)).fetchone()
            if not item:
                fail("Không có mặt hàng")
            if item["group_name"] in DAILY_USAGE_GROUPS:
                fail("Đá và than chỉ ghi lượng dùng theo ngày")
            kind = clean(data.get("kind"), 20)
            if kind not in ("receipt", "sale", "waste", "gift", "return"):
                fail("Loại xuất nhập không hợp lệ")
            q = quantity(data.get("quantity"), True)
            if kind in ("sale", "waste", "gift"):
                q = -q
            if kind in ("waste", "gift", "return") and not data.get("reason"):
                fail("Cần ghi lý do")
            cur = con.execute(
                "INSERT INTO stock_moves(item_id,quantity,kind,reason,reference,created_at,created_by) VALUES(?,?,?,?,?,?,?)",
                (item_id, str(q), kind, clean(data.get("reason", ""), 200, False),
                 clean(data.get("reference", ""), 100, False), now(), uid))
            audit(con, uid, "create", "stock_moves", cur.lastrowid, kind)
            return {"id": cur.lastrowid, "balance": str(balance(con, item_id))}
        if path == "/api/stock-counts":
            self.require(user, "owner", "manager", "stock")
            item_id = int(data.get("item_id", 0))
            item = con.execute("SELECT group_name FROM items WHERE id=?", (item_id,)).fetchone()
            if not item:
                fail("Không có mặt hàng")
            if item["group_name"] in DAILY_USAGE_GROUPS:
                fail("Đá và than chỉ ghi lượng dùng theo ngày")
            counted = quantity(data.get("counted_qty"))
            book = balance(con, item_id)
            cur = con.execute(
                "INSERT INTO stock_counts(item_id,book_qty,counted_qty,difference,note,created_at,created_by) VALUES(?,?,?,?,?,?,?)",
                (item_id, str(book), str(counted), str(counted - book),
                 clean(data.get("note", ""), 200, False), now(), uid))
            audit(con, uid, "create", "stock_counts", cur.lastrowid)
            return {"id": cur.lastrowid, "difference": str(counted - book)}
        match = re.fullmatch(r"/api/stock-counts/(\d+)/approve", path)
        if match:
            self.require(user, "owner", "manager")
            cid = int(match.group(1))
            count = con.execute("SELECT * FROM stock_counts WHERE id=?", (cid,)).fetchone()
            if not count or count["status"] != "pending":
                fail("Phiếu kiểm kê không chờ duyệt")
            current = balance(con, count["item_id"])
            if current != Decimal(count["book_qty"]):
                fail("Tồn sổ đã thay đổi; cần kiểm kê lại")
            diff = Decimal(count["difference"])
            if diff:
                con.execute(
                    "INSERT INTO stock_moves(item_id,quantity,kind,reason,reference,created_at,created_by) VALUES(?,?,?,?,?,?,?)",
                    (count["item_id"], str(diff), "count_adjustment", clean(data.get("reason"), 200),
                     f"COUNT-{cid}", now(), uid))
            con.execute("UPDATE stock_counts SET status='approved',reviewed_at=?,reviewed_by=? WHERE id=?",
                        (now(), uid, cid))
            audit(con, uid, "approve", "stock_counts", cid, clean(data.get("reason", ""), 200, False))
            return {"id": cid}
        if path == "/api/work-shifts":
            self.require(user, "owner", "manager")
            employee_id = int(data.get("user_id", 0))
            if not con.execute("SELECT 1 FROM users WHERE id=? AND active=1", (employee_id,)).fetchone():
                fail("Không có nhân viên")
            start, end = iso_time(data.get("starts_at")), iso_time(data.get("ends_at"))
            if datetime.fromisoformat(start) >= datetime.fromisoformat(end):
                fail("Giờ kết thúc phải sau giờ bắt đầu")
            cur = con.execute("INSERT INTO work_shifts(user_id,starts_at,ends_at,note) VALUES(?,?,?,?)",
                              (employee_id, start, end, clean(data.get("note", ""), 200, False)))
            audit(con, uid, "create", "work_shifts", cur.lastrowid)
            return {"id": cur.lastrowid}
        match = re.fullmatch(r"/api/work-shifts/(\d+)/(check-in|check-out)", path)
        if match:
            wid = int(match.group(1))
            shift = con.execute("SELECT * FROM work_shifts WHERE id=?", (wid,)).fetchone()
            if not shift or shift["user_id"] != uid:
                fail("Không có ca làm hoặc không có quyền", 403)
            if match.group(2) == "check-in":
                if shift["checked_in_at"]:
                    fail("Đã chấm vào")
                con.execute("UPDATE work_shifts SET checked_in_at=? WHERE id=?", (now(), wid))
            else:
                if not shift["checked_in_at"] or shift["checked_out_at"]:
                    fail("Cần chấm vào trước, hoặc đã chấm ra")
                con.execute("UPDATE work_shifts SET checked_out_at=? WHERE id=?", (now(), wid))
            audit(con, uid, match.group(2), "work_shifts", wid)
            return {"id": wid}
        if path == "/api/incidents":
            self.require(user, "owner", "manager", "cashier")
            amount = money(data.get("amount", 0))
            if amount < 0:
                fail("Giá trị không âm")
            employee = data.get("user_id")
            cur = con.execute(
                "INSERT INTO order_incidents(bill_ref,category,description,amount,user_id,created_at,created_by) VALUES(?,?,?,?,?,?,?)",
                (clean(data.get("bill_ref"), 80), clean(data.get("category"), 40),
                 clean(data.get("description"), 500), amount, int(employee) if employee else None, now(), uid))
            audit(con, uid, "create", "order_incidents", cur.lastrowid)
            return {"id": cur.lastrowid}
        match = re.fullmatch(r"/api/incidents/(\d+)/resolve", path)
        if match:
            self.require(user, "owner", "manager")
            iid = int(match.group(1))
            reason = clean(data.get("reason"), 200)
            changed = con.execute("UPDATE order_incidents SET status='resolved',description=description || ? WHERE id=? AND status='open'",
                                  ("\nXử lý: " + reason, iid)).rowcount
            if not changed:
                fail("Sự cố không còn mở")
            audit(con, uid, "resolve", "order_incidents", iid, reason)
            return {"id": iid}
        if path == "/api/sales-import":
            self.require(user, "owner", "manager", "cashier")
            sid = int(data.get("shift_id", 0))
            shift = con.execute("SELECT locked_at FROM cash_shifts WHERE id=?", (sid,)).fetchone()
            if not shift or shift["locked_at"]:
                fail("Ca không tồn tại hoặc đã khóa")
            if user["role"] == "cashier":
                owner = con.execute("SELECT opened_by FROM cash_shifts WHERE id=?", (sid,)).fetchone()
                if owner["opened_by"] != uid:
                    fail("Thu ngân chỉ được nhập vào ca của mình", 403)
            rows = data.get("rows")
            if not isinstance(rows, list) or len(rows) > 2000:
                fail("Tối đa 2000 dòng mỗi lần nhập")
            prepared = []
            seen = set()
            for index, row in enumerate(rows, 1):
                if not isinstance(row, dict):
                    fail(f"Dòng {index}: dữ liệu không hợp lệ")
                source = clean(row.get("source_row_id"), 100)
                if source in seen:
                    fail(f"Dòng {index}: trùng mã nguồn trong file")
                seen.add(source)
                existing = con.execute("SELECT shift_id FROM sales_imports WHERE source_row_id=?", (source,)).fetchone()
                if existing and existing["shift_id"] != sid:
                    fail(f"Dòng {index}: mã nguồn đã thuộc ca khác")
                method = clean(row.get("method"), 20).lower()
                if method not in ("cash", "bank"):
                    fail(f"Dòng {index}: phương thức chỉ cash hoặc bank")
                q = quantity(row.get("quantity", 0))
                amount = money(row.get("amount", 0))
                if amount < 0:
                    fail(f"Dòng {index}: doanh thu không âm")
                code = clean(row.get("item_code", ""), 40, False).upper()
                item = con.execute("SELECT * FROM items WHERE code=?", (code,)).fetchone() if code else None
                if code and not item:
                    fail(f"Dòng {index}: mã hàng chưa có trong danh mục")
                if item and item["group_name"] in TRACKED_GROUPS and q <= 0:
                    fail(f"Dòng {index}: số lượng hàng bán trực tiếp phải lớn hơn 0")
                prepared.append((source, item, q, amount, method))
            inserted = 0
            for source, item, q, amount, method in prepared:
                cur = con.execute(
                    "INSERT OR IGNORE INTO sales_imports(source_row_id,shift_id,item_id,quantity,amount,method,created_at,created_by) VALUES(?,?,?,?,?,?,?,?)",
                    (source, sid, item["id"] if item else None, str(q), amount, method, now(), uid))
                if cur.rowcount:
                    inserted += 1
                    if item and item["group_name"] in TRACKED_GROUPS:
                        con.execute(
                            "INSERT INTO stock_moves(item_id,quantity,kind,reason,reference,shift_id,created_at,created_by) VALUES(?,?,?,?,?,?,?,?)",
                            (item["id"], str(-q), "sale", "Bán theo CSV", source, sid, now(), uid))
            audit(con, uid, "import", "sales_imports", sid, f"{inserted} dòng mới")
            return {"inserted": inserted, "skipped": len(prepared) - inserted}
        fail("Không tìm thấy", 404)


if __name__ == "__main__":
    init_db()
    host = os.environ.get("RESTAURANT_HOST", "127.0.0.1")
    port = int(os.environ.get("RESTAURANT_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), Handler)
    cert, key = os.environ.get("RESTAURANT_TLS_CERT"), os.environ.get("RESTAURANT_TLS_KEY")
    if bool(cert) != bool(key):
        raise SystemExit("Cần cả RESTAURANT_TLS_CERT và RESTAURANT_TLS_KEY")
    if cert and key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    elif host not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("Truy cập qua mạng cần HTTPS: đặt RESTAURANT_TLS_CERT và RESTAURANT_TLS_KEY")
    scheme = "https" if cert else "http"
    print(f"Restaurant control: {scheme}://{host}:{port}")
    server.serve_forever()
