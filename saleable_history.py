"""Read-only day, week and month history for saleable inventory."""

import json
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from menu_catalog import canonical_code

from zone_shift_report import TRACKED, business_day, converted_quantity, fmt, number

GROUP_ORDER = {name: index for index, name in enumerate(
    ("beer", "liquor", "soft_drink", "water", "rice_paper", "peanuts", "tobacco"))}


def period_bounds(period, anchor):
    chosen = date.fromisoformat(anchor)
    if chosen.isoformat() != anchor or period not in ("day", "week", "month"):
        raise ValueError("Bộ lọc ngày, tuần hoặc tháng không hợp lệ")
    if period == "day":
        return chosen, chosen
    if period == "week":
        first = chosen - timedelta(days=chosen.weekday())
        return first, first + timedelta(days=6)
    first = chosen.replace(day=1)
    next_month = first.replace(year=first.year+1, month=1) if first.month == 12 else first.replace(month=first.month+1)
    return first, next_month - timedelta(days=1)


def _sold_from_sync(con, day, catalog, cutoff):
    next_day = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
    sold = defaultdict(Decimal)
    unknown = set()
    invoices = set()
    for row in con.execute("""SELECT i.ref_id,i.ref_date,d.item_code,d.quantity,d.unit_name
        FROM cukcuk_invoice_items d JOIN cukcuk_invoices i ON i.ref_id=d.ref_id
        WHERE i.payment_status=3 AND substr(i.ref_date,1,10) BETWEEN ? AND ?""", (day, next_day)):
        if business_day(row["ref_date"], cutoff) != day:
            continue
        invoices.add(row["ref_id"])
        code = canonical_code(row["item_code"])
        item = catalog.get(code)
        if not item:
            continue
        try:
            amount = converted_quantity({"Quantity": row["quantity"], "UnitName": row["unit_name"],
                                         "ItemCode": row["item_code"]}, item)
        except ValueError:
            amount = None
        if amount is None:
            unknown.add(code)
        else:
            sold[code] += amount
    return sold, unknown, len(invoices)


def history_report(con, period, anchor, stock_report, cutoff=5):
    first, last = period_bounds(period, anchor)
    catalog = {row["code"].upper(): dict(row) for row in con.execute(
        "SELECT code,name,group_name,unit,units_per_carton FROM items WHERE active=1")
        if row["group_name"] in TRACKED}
    days = []
    current = first
    while current <= last:
        day = current.isoformat()
        stock_rows = [row for row in stock_report(con, day) if row["group"] in TRACKED]
        snapshot_row = con.execute("SELECT report_json FROM zone_shift_reports WHERE day=? ORDER BY id DESC LIMIT 1",
                                   (day,)).fetchone()
        snapshot = json.loads(snapshot_row["report_json"]) if snapshot_row else None
        synced = bool(stock_rows and stock_rows[0]["synced"])
        sold, unknown, invoice_count = _sold_from_sync(con, day, catalog, cutoff) if synced and not snapshot else ({}, set(), 0)
        if snapshot:
            sold = defaultdict(Decimal)
            for raw_code, value in snapshot.get("sold", {}).items():
                sold[canonical_code(raw_code)] += number(value)
            unknown = {canonical_code(code) for code in snapshot.get("unknown_units", [])}
            invoice_count = snapshot.get("invoice_count", 0)
        has_counts = bool(con.execute("""SELECT 1 FROM daily_stock_counts c JOIN items i ON i.id=c.item_id
            WHERE c.day=? AND i.active=1 AND i.group_name IN ('beer','liquor','soft_drink','water','rice_paper','peanuts','tobacco') LIMIT 1""",
            (day,)).fetchone())
        has_data = bool(has_counts or invoice_count or snapshot)
        coverage = bool(snapshot or synced)
        rows = []
        if has_data:
            for row in sorted(stock_rows, key=lambda r: (GROUP_ORDER.get(r["group"], 99), r["name"].casefold())):
                code = row["code"].upper()
                opening = row["opening"] if row["has_previous_closing"] else None
                incoming = row["incoming"]
                closing = row["closing"]
                sale = sold.get(code, Decimal(0)) if coverage and code not in unknown else None
                variance = None
                if opening is not None and incoming is not None and closing is not None and sale is not None:
                    expected = (number(opening) + number(row["received"]) -
                                number(row["waste_gift"]) - sale)
                    variance = number(closing) - expected
                rows.append({"code": code, "name": row["name"], "group": row["group"], "unit": row["unit"],
                             "opening": opening, "incoming": incoming,
                             "sold": fmt(sale) if sale is not None else None, "closing": closing,
                             "variance": fmt(variance) if variance is not None else None,
                             "unit_unknown": code in unknown})
        if not has_data:
            status = "no_data"
        elif not coverage:
            status = "unsynced"
        elif any(row["unit_unknown"] for row in rows):
            status = "unit_unknown"
        elif any(row["variance"] is not None and number(row["variance"]) != 0 for row in rows):
            status = "difference"
        elif any(row["variance"] is None for row in rows):
            status = "incomplete"
        else:
            status = "ok"
        days.append({"day": day, "status": status, "source": "report" if snapshot else "sync" if synced else "none",
                     "invoice_count": invoice_count, "rows": rows})
        current += timedelta(days=1)
    return {"period": period, "anchor": anchor, "from": first.isoformat(), "to": last.isoformat(), "days": days}
