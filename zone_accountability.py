"""Zone ownership and evidence-based order discrepancy calculations."""

import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


CHECK_GROUPS = ("beer", "liquor", "water", "rice_paper", "peanuts", "tobacco")
GROUP_LABELS = {
    "beer": "Bia", "liquor": "Rượu", "water": "Nước",
    "rice_paper": "Bánh tráng", "peanuts": "Đậu phộng", "tobacco": "Thuốc",
}


def table_number(value):
    """Use the numeric table identifier for both '101' and 'Bàn 101'."""
    match = re.fullmatch(r"\s*(?:bàn\s*)?(\d+)\s*", str(value), re.IGNORECASE)
    if not match:
        return None
    digits = match.group(1).lstrip("0")
    return digits or None


def init_zone_db(con):
    con.executescript("""
        CREATE TABLE IF NOT EXISTS zones(
          id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE, active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS zone_tables(
          table_name TEXT PRIMARY KEY, zone_id INTEGER NOT NULL REFERENCES zones(id),
          updated_at TEXT NOT NULL, updated_by INTEGER NOT NULL REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS zone_assignments(
          id INTEGER PRIMARY KEY, zone_id INTEGER NOT NULL REFERENCES zones(id),
          user_id INTEGER NOT NULL REFERENCES users(id),
          starts_at TEXT NOT NULL, ends_at TEXT NOT NULL,
          active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_zone_assignment_window
          ON zone_assignments(zone_id,starts_at,ends_at);
        CREATE TABLE IF NOT EXISTS zone_observations(
          id INTEGER PRIMARY KEY, table_name TEXT NOT NULL, zone_id INTEGER REFERENCES zones(id),
          observed_at TEXT NOT NULL, observed_by INTEGER NOT NULL REFERENCES users(id),
          order_as_of TEXT NOT NULL, mapping_status TEXT NOT NULL,
          assigned_staff_json TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'open', resolution_note TEXT NOT NULL DEFAULT '',
          resolved_at TEXT, resolved_by INTEGER REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS zone_observation_items(
          observation_id INTEGER NOT NULL REFERENCES zone_observations(id),
          group_name TEXT NOT NULL, observed_qty TEXT NOT NULL,
          ordered_qty TEXT, surplus_qty TEXT,
          PRIMARY KEY(observation_id,group_name)
        );
    """)


def _decimal(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Số lượng không hợp lệ")
    if not result.is_finite() or result < 0:
        raise ValueError("Số lượng không hợp lệ")
    return result


def _number(value):
    return format(value.normalize(), "f")


def order_groups_for_table(rows, table_name):
    """Aggregate CUKCUK item groups, keeping water and soft drinks together."""
    totals = {group: Decimal(0) for group in CHECK_GROUPS}
    for row in rows:
        if row["table"] != table_name:
            continue
        group = "water" if row["group"] in ("water", "soft_drink") else row["group"]
        if group in totals:
            totals[group] += _decimal(row["quantity"])
    return totals


def staff_at(assignments, zone_id, at):
    if zone_id is None:
        return []
    moment = datetime.fromisoformat(at.replace("Z", "+00:00"))
    result = []
    seen = set()
    for row in assignments:
        if row["zone_id"] != zone_id or not row["active"]:
            continue
        start = datetime.fromisoformat(row["starts_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(row["ends_at"].replace("Z", "+00:00"))
        if start <= moment < end and row["user_id"] not in seen:
            seen.add(row["user_id"])
            result.append({"id": row["user_id"], "name": row["user_name"]})
    return sorted(result, key=lambda item: (item["name"], item["id"]))


def build_live_review(report, zones, table_mappings, assignments, pack_sizes=None):
    """Attach zone and staff context to active CUKCUK tables without blaming staff."""
    zone_by_id = {row["id"]: row for row in zones if row["active"]}
    pack_sizes = pack_sizes or {}
    zone_by_table = {table_number(row["table_name"]): row["zone_id"] for row in table_mappings}
    result = []
    for table in report["tables"]:
        label = table["table"]
        product_items = [{"code": row.get("code") or "", "name": row.get("name") or row.get("code") or "Hàng",
                       "group": "water" if row["group"] in ("water", "soft_drink") else row["group"],
                       "quantity": row["quantity"], "unit": row.get("unit") or "",
                       "units_per_carton": pack_sizes.get((row.get("code") or "").upper()),
                       "unit_status": row.get("unit_status", "unknown")}
                       for row in report["rows"] if row["table"] == label and row["group"] in
                       ("beer", "water", "soft_drink", "tobacco")]
        beer_items = [item for item in product_items if item["group"] == "beer"]
        zone_id = zone_by_table.get(table_number(label))
        zone = zone_by_id.get(zone_id)
        mapped = bool(zone) and not table["combined_table"]
        can_evaluate = table["mapping_status"] == "mapped" and not table["combined_table"]
        missing = []
        if can_evaluate:
            if table["no_beer"]:
                missing.append("beer")
            missing.extend(table["missing_required"])
        result.append({
            "table": label, "zone_id": zone_id if mapped else None,
            "zone_name": zone["name"] if mapped else None,
            "staff": staff_at(assignments, zone_id, report["as_of"]) if mapped else [],
            "mapping_status": "combined" if table["combined_table"] else table["mapping_status"],
            "missing_order_groups": missing,
            "quantities": table["quantities"],
            "beer_items": beer_items,
            "product_items": product_items,
        })
    return result


def compare_observation(report, table_name, observed):
    """Only compare checked groups on a clearly identified open table."""
    table = next((row for row in report["tables"] if row["table"] == table_name), None)
    if table is None:
        raise ValueError("Bàn không còn order đang mở trên CUKCUK")
    if not observed or set(observed) - set(CHECK_GROUPS):
        raise ValueError("Hãy nhập ít nhất một nhóm hàng hợp lệ")
    can_compare = table["mapping_status"] == "mapped" and not table["combined_table"]
    ordered = order_groups_for_table(report["rows"], table_name) if can_compare else {}
    lines = []
    for group in CHECK_GROUPS:
        if group not in observed:
            continue
        actual = _decimal(observed[group])
        if actual != actual.to_integral_value():
            raise ValueError("Số kiểm thực tế phải là số nguyên")
        sold = ordered.get(group)
        surplus = max(Decimal(0), actual - sold) if sold is not None else None
        lines.append({"group": group, "observed_qty": _number(actual),
                      "ordered_qty": _number(sold) if sold is not None else None,
                      "surplus_qty": _number(surplus) if surplus is not None else None})
    return lines, "mapped" if can_compare else ("combined" if table["combined_table"] else "unknown")


def config_snapshot(con):
    zones = [dict(row) for row in con.execute("SELECT id,name,active FROM zones ORDER BY name")]
    tables = [dict(row) for row in con.execute("""SELECT t.table_name,t.zone_id,z.name zone_name
        FROM zone_tables t JOIN zones z ON z.id=t.zone_id WHERE z.active=1 ORDER BY z.name,t.table_name""")]
    assignments = [dict(row) for row in con.execute("""SELECT a.id,a.zone_id,a.user_id,
        u.display_name user_name,a.starts_at,a.ends_at,a.active
        FROM zone_assignments a JOIN users u ON u.id=a.user_id
        JOIN zones z ON z.id=a.zone_id WHERE z.active=1 ORDER BY a.starts_at DESC,a.id DESC LIMIT 500""")]
    observations = [dict(row) for row in con.execute("""SELECT o.id,o.table_name,o.zone_id,
        z.name zone_name,o.observed_at,o.order_as_of,o.mapping_status,o.assigned_staff_json,
        o.status,o.resolution_note,u.display_name observer_name
        FROM zone_observations o LEFT JOIN zones z ON z.id=o.zone_id
        JOIN users u ON u.id=o.observed_by ORDER BY o.id DESC LIMIT 100""")]
    for row in observations:
        row["assigned_staff"] = json.loads(row.pop("assigned_staff_json"))
        row["items"] = [dict(item) for item in con.execute("""SELECT group_name,observed_qty,ordered_qty,surplus_qty
            FROM zone_observation_items WHERE observation_id=? ORDER BY group_name""", (row["id"],))]
    return {"zones": zones, "tables": tables, "assignments": assignments,
            "observations": observations}
