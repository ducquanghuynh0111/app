"""Small, explicit projection of live CUKCUK orders for stock control."""

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from menu_catalog import canonical_code
import unicodedata


TRACKED_GROUPS = frozenset({
    "beer", "liquor", "soft_drink", "water", "tobacco", "rice_paper", "peanuts",
})
ACTIVE_ORDER_STATUSES = frozenset({1, 3, 7, 8})


def _quantity(value):
    try:
        quantity = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return quantity if quantity.is_finite() and quantity > 0 else None


def _active(order):
    try:
        return int(order.get("Status") or 0) in ACTIVE_ORDER_STATUSES
    except (TypeError, ValueError):
        return False


def _unit_kind(value):
    plain = "".join(char for char in unicodedata.normalize("NFD", str(value or "").casefold())
                    if unicodedata.category(char) != "Mn").strip()
    if plain.startswith(("thung", "ket ", "ket")):
        return "carton"
    if plain.startswith("lon"):
        return "lon"
    if plain.startswith("chai"):
        return "chai"
    if plain.startswith("cay"):
        return "carton"
    if plain.startswith("goi"):
        return "goi"
    return None


def project_table_items(orders, catalog_by_id, groups_by_code,
                        pack_sizes_by_code=None, base_units_by_code=None, names_by_code=None):
    """Return tracked quantities per table and unmapped CUKCUK item IDs.

    catalog_by_id maps CUKCUK ItemId to the catalog Code. groups_by_code maps
    that Code to one of the configured local stock groups. A table label is
    kept intact because one order may span several tables.
    """
    totals = defaultdict(Decimal)
    pack_sizes_by_code = pack_sizes_by_code or {}
    base_units_by_code = base_units_by_code or {}
    names_by_code = names_by_code or {}
    unmapped = set()
    unknown_tables = set()
    seen_details = set()
    for order in orders:
        if not _active(order):
            continue
        order_id = str(order.get("Id") or "").strip()
        table = str(order.get("TableName") or "").strip()
        if not order_id or not table:
            continue
        for detail in order.get("OrderDetails") or ():
            if detail.get("ParentId") or detail.get("AdditionId"):
                continue
            detail_id = str(detail.get("Id") or "").strip()
            item_id = str(detail.get("ItemId") or "").strip().lower()
            if not detail_id or not item_id or (order_id, detail_id) in seen_details:
                continue
            seen_details.add((order_id, detail_id))
            quantity = _quantity(detail.get("Quantity"))
            if quantity is None:
                continue
            raw_code = str(catalog_by_id.get(item_id) or "").strip().upper()
            code = canonical_code(raw_code)
            group = groups_by_code.get(code)
            if not code:
                unmapped.add(item_id)
                unknown_tables.add(table)
                continue
            if not group:
                if code in {"BATR", "DAUPHONG", "DAPH"}:
                    unmapped.add(item_id)
                    unknown_tables.add(table)
                continue
            if group not in TRACKED_GROUPS:
                continue
            name = str(names_by_code.get(code) or detail.get("ItemName") or code).strip()[:120]
            unit = str(detail.get("UnitName") or "").strip()
            base_unit = str(base_units_by_code.get(code) or "").strip()
            unit_status = "known"
            if group in ("beer", "soft_drink", "water", "tobacco"):
                kind = _unit_kind(unit)
                allowed = ("goi",) if group == "tobacco" else ("lon", "chai")
                if kind == "carton":
                    factor = _quantity(pack_sizes_by_code.get(code))
                    if factor is not None and _unit_kind(base_unit) in allowed:
                        quantity *= factor
                        unit = base_unit
                    else:
                        unit_status = "unknown"
                        unknown_tables.add(table)
                elif kind in allowed:
                    unit = base_unit if raw_code != code and _unit_kind(base_unit) in allowed else \
                        {"lon":"Lon", "chai":"Chai", "goi":"Gói"}[kind]
                elif _unit_kind(base_unit) in allowed:
                    unit = base_unit
                else:
                    unit_status = "unknown"
            totals[(table, group, code, name, unit, unit_status)] += quantity
    rows = [
        {"table": table, "group": group, "code": code, "name": name,
         "quantity": format(quantity.normalize(), "f"), "unit": unit,
         "unit_status": unit_status}
        for (table, group, code, name, unit, unit_status), quantity in sorted(totals.items())
    ]
    return rows, len(unmapped), unknown_tables


def project_table_status(orders, item_rows, unknown_tables=None):
    """Show every table with an active order, including tables with no tracked item."""
    tables = {}
    for order in orders:
        if not _active(order):
            continue
        label = str(order.get("TableName") or "").strip()
        if not label:
            continue
        tables.setdefault(label, {group: Decimal(0) for group in TRACKED_GROUPS})
    for row in item_rows:
        tables[row["table"]][row["group"]] += Decimal(row["quantity"])
    result = []
    for label, quantities in sorted(tables.items()):
        result.append({
            "table": label,
            "mapping_status": "unknown" if label in (unknown_tables or set()) else "mapped",
            "quantities": {group: format(quantities[group].normalize(), "f") for group in sorted(TRACKED_GROUPS)},
            "missing_required": [group for group in ("rice_paper", "peanuts") if quantities[group] == 0],
            "no_beer": quantities["beer"] == 0,
            "combined_table": "," in label or ";" in label,
        })
    return result
