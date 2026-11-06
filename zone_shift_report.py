"""Post-service stock and zone review using finalized CUKCUK invoices."""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from menu_catalog import canonical_code
import json

from zone_accountability import table_number
from table_merchandise import _unit_kind

LOCAL_TZ = timezone(timedelta(hours=7))
TRACKED = {"beer", "liquor", "soft_drink", "water", "rice_paper", "peanuts", "tobacco"}
TOBACCO = {"TNN", "TM"}


def number(value):
    try:
        n = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Số lượng không hợp lệ")
    if not n.is_finite() or n < 0:
        raise ValueError("Số lượng không hợp lệ")
    return n


def fmt(value):
    return format(value.normalize(), "f")


def business_day(moment, cutoff=5):
    if isinstance(moment, str):
        moment = datetime.fromisoformat(moment.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=LOCAL_TZ)
    return (moment.astimezone(LOCAL_TZ) - timedelta(hours=cutoff)).date().isoformat()


def split_pack(quantity, size, label, loose_label="đơn vị"):
    if size is None or number(size) <= 0:
        return f"{fmt(number(quantity))} đơn vị (chưa rõ quy cách)"
    count, remainder = divmod(number(quantity), number(size))
    parts = []
    if count:
        parts.append(f"{int(count)} {label}")
    if remainder or not parts:
        parts.append(f"{fmt(remainder)} {loose_label}")
    return " + ".join(parts)


def init_db(con):
    con.executescript("""
        CREATE TABLE IF NOT EXISTS zone_tobacco_allocations(
          day TEXT NOT NULL, zone_id INTEGER NOT NULL REFERENCES zones(id),
          item_code TEXT NOT NULL CHECK(item_code IN ('TNN','TM')),
          issued TEXT, returned TEXT, ending TEXT,
          updated_at TEXT NOT NULL, updated_by INTEGER NOT NULL REFERENCES users(id),
          PRIMARY KEY(day,zone_id,item_code)
        );
        CREATE TABLE IF NOT EXISTS zone_shift_reports(
          id INTEGER PRIMARY KEY, day TEXT NOT NULL, generated_at TEXT NOT NULL,
          generated_by INTEGER NOT NULL REFERENCES users(id), report_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_zone_shift_day ON zone_shift_reports(day,id);
        CREATE TABLE IF NOT EXISTS zone_shift_notes(
          report_id INTEGER NOT NULL REFERENCES zone_shift_reports(id),
          invoice_id TEXT NOT NULL, note TEXT NOT NULL,
          updated_at TEXT NOT NULL, updated_by INTEGER NOT NULL REFERENCES users(id),
          PRIMARY KEY(report_id,invoice_id)
        );
    """)


def _invoice_moment(invoice):
    return invoice.get("RefDate") or invoice.get("InvoiceDate") or invoice.get("CreatedDate")


def converted_quantity(detail, item):
    qty = number(detail.get("Quantity"))
    unit = _unit_kind(detail.get("UnitName"))
    base = _unit_kind(item["unit"])
    if unit == "carton":
        size = item.get("units_per_carton")
        return qty * number(size) if size is not None and number(size) > 0 and base else None
    if unit is not None and unit == base:
        return qty
    raw_code = str(detail.get("ItemCode") or "").strip().upper()
    if raw_code and canonical_code(raw_code) != raw_code and unit in ("lon", "chai") and base in ("lon", "chai"):
        return qty
    return None


def project_invoices(invoices, day, zones, zone_tables, catalog, cutoff=5):
    """Return sales and missing-order evidence per invoice; no customer details."""
    by_code = {item["code"].upper(): item for item in catalog}
    zone_by_id = {zone["id"]: zone for zone in zones if zone["active"]}
    mapping = {str(row["table_name"]): row["zone_id"] for row in zone_tables}
    sold = defaultdict(Decimal)
    zone_sold = defaultdict(lambda: defaultdict(Decimal))
    warnings, closed_invoices, unknown_units, unmapped = [], [], set(), set()
    processed = set()
    finalized_count = 0
    for invoice in invoices:
        ref_id = str(invoice.get("RefId") or "")
        moment = _invoice_moment(invoice)
        if not ref_id or ref_id in processed or not moment or business_day(moment, cutoff) != day:
            continue
        processed.add(ref_id)
        if invoice.get("PaymentStatus") != 3 or invoice.get("OrderType") not in (None, 1):
            continue
        finalized_count += 1
        table = table_number(invoice.get("TableName"))
        zone_id = mapping.get(table) if table else None
        zone = zone_by_id.get(zone_id)
        quantities = defaultdict(Decimal)
        invoice_unknown = False
        ordered_items = []
        for detail in invoice.get("SAInvoiceDetails") or []:
            if detail.get("ParentId") or detail.get("AdditionId"):
                continue
            code = canonical_code(detail.get("ItemCode"))
            item = by_code.get(code)
            raw_quantity = detail.get("Quantity")
            try:
                display_quantity = fmt(number(raw_quantity))
            except ValueError:
                display_quantity = str(raw_quantity or "-")[:32]
            ordered_items.append({"name": str(detail.get("ItemName") or (item or {}).get("name") or code or "Món chưa rõ tên")[:120],
                                  "quantity": display_quantity,
                                  "unit": str(detail.get("UnitName") or "")[:40]})
            if item is None:
                if code:
                    unmapped.add(code)
                    invoice_unknown = True
                continue
            if item["group_name"] not in TRACKED:
                continue
            try:
                qty = converted_quantity(detail, item)
            except ValueError:
                qty = None
            if qty is None:
                unknown_units.add(code)
                invoice_unknown = True
                continue
            sold[code] += qty
            quantities[code] += qty
            if zone:
                zone_sold[zone_id][code] += qty
        if not table or not zone:
            continue
        groups = {by_code[code]["group_name"] for code, amount in quantities.items() if amount > 0}
        missing = [label for group, label in (("beer", "Bia"), ("rice_paper", "Bánh tráng"),
                                               ("peanuts", "Đậu phộng")) if group not in groups]
        closed_invoices.append({"invoice_id": ref_id, "invoice_no": str(invoice.get("RefNo") or "")[:80],
                                "table": table, "zone_id": zone_id, "zone_name": zone["name"],
                                "invoice_at": str(moment)[:40], "items": ordered_items,
                                "missing": missing, "uncertain": invoice_unknown})
        if missing or invoice_unknown:
            warnings.append({"invoice_id": ref_id, "invoice_no": str(invoice.get("RefNo") or "")[:80],
                             "table": table, "zone_id": zone_id, "zone_name": zone["name"],
                             "missing": missing, "uncertain": invoice_unknown})
    zone_rows = []
    for zone_id, zone in zone_by_id.items():
        items = []
        for code, amount in sorted(zone_sold[zone_id].items()):
            item = by_code[code]
            group = item["group_name"]
            items.append({"code": code, "name": item["name"], "group": group,
                          "quantity": fmt(amount), "unit": item["unit"],
                          "packs": split_pack(amount, item.get("units_per_carton"),
                                              "cây" if group == "tobacco" else "thùng", item["unit"].lower())
                          if group in ("beer", "tobacco") else None})
        zone_rows.append({"zone_id": zone_id, "name": zone["name"], "items": items,
                          "warnings": sum(w["zone_id"] == zone_id for w in warnings)})
    return {"day": day, "sold": {code: fmt(qty) for code, qty in sold.items()},
            "zones": zone_rows, "warnings": warnings, "closed_invoices": closed_invoices,
            "unknown_units": sorted(unknown_units),
            "unmapped_codes": sorted(unmapped), "invoice_count": finalized_count}


def reconcile_stock(rows, sold, unknown_units, unknown_all=False):
    result = []
    for row in rows:
        if row["group"] not in TRACKED:
            continue
        code = row["code"].upper()
        ready = (row["has_previous_closing"] and row["incoming"] is not None and
                 row["closing"] is not None and code not in unknown_units and not unknown_all)
        expected = variance = None
        if ready:
            expected = number(row["opening"]) + number(row["received"]) - number(row["waste_gift"]) - number(sold.get(code, 0))
            variance = number(row["closing"]) - expected
        result.append({"code": code, "name": row["name"], "group": row["group"], "unit": row["unit"],
                       "opening": row["opening"] if row["has_previous_closing"] else None,
                       "incoming": row["incoming"], "closing": row["closing"], "sold": sold.get(code, "0"),
                       "expected": fmt(expected) if ready else None, "variance": fmt(variance) if ready else None,
                       "status": "unknown" if not ready else "ok" if variance == 0 else "difference"})
    return result


def tobacco_balance(issued, returned, ending, ordered):
    if issued is None or returned is None or ending is None:
        return None
    return fmt(number(issued) - number(returned) - number(ending) - number(ordered))
