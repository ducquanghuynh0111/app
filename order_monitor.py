"""Poll CUKCUK orders and maintain a runner queue with timed reminders."""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

import app
from cukcuk_sync import Client, CukcukError

NEW_ACTIVE = {1, 3, 8}


def _stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")


def _safe_text(value, limit: int = 100) -> str:
    return str(value or "").strip()[:limit]


def kds_done_statuses() -> set[int]:
    if os.environ.get("RUNNER_COMPLETION_MODE", "runner") != "kds":
        return set()
    raw = os.environ.get("CUKCUK_KDS_DONE_STATUSES", "")
    return {int(part.strip()) for part in raw.split(",") if part.strip()}


def save_order(con, order: dict, observed_at: str, announce: bool = True) -> int:
    order_id = _safe_text(order.get("Id"), 80)
    if not order_id:
        raise CukcukError("Order thiếu mã")
    status = int(order.get("Status", 0))
    con.execute("""INSERT INTO runner_orders(order_id,order_no,table_name,order_status,last_seen_at)
        VALUES(?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET order_no=excluded.order_no,
        table_name=excluded.table_name,order_status=excluded.order_status,last_seen_at=excluded.last_seen_at""",
        (order_id, _safe_text(order.get("No"), 40), _safe_text(order.get("TableName"), 80), status, observed_at))
    if status == 5:
        con.execute("UPDATE runner_items SET canceled_at=? WHERE order_id=? AND served_at IS NULL AND canceled_at IS NULL",
                    (observed_at, order_id))
        return 0
    current_ids = set()
    created = 0
    done_statuses = kds_done_statuses()
    for detail in order.get("OrderDetails") or []:
        if detail.get("ParentId") or detail.get("AdditionId"):
            continue
        source_id = _safe_text(detail.get("Id"), 80)
        name = _safe_text(detail.get("ItemName"), 120)
        if not source_id or not name:
            continue
        detail_id = order_id + ":" + source_id
        try:
            quantity = Decimal(str(detail.get("Quantity", 0)))
        except InvalidOperation as exc:
            raise CukcukError("Số lượng món không hợp lệ") from exc
        if not quantity.is_finite() or quantity <= 0 or quantity > 1000:
            continue
        qty = format(quantity.normalize(), "f")
        item_key = _safe_text(detail.get("ItemId"), 80) or "name:" + name.casefold()
        kds_status = detail.get("Status")
        kds_status = int(kds_status) if kds_status is not None else None
        current_ids.add(detail_id)
        existing = con.execute("SELECT quantity,source_quantity,served_quantity,canceled_at,served_at,kds_status FROM runner_items WHERE detail_id=?", (detail_id,)).fetchone()
        if existing is None:
            completed = kds_status in done_statuses if kds_status is not None else False
            con.execute("""INSERT INTO runner_items(detail_id,order_id,item_name,item_key,quantity,source_quantity,served_quantity,
                first_seen_at,served_at,kds_status) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (detail_id, order_id, name, item_key, "0" if completed else qty, qty,
                 qty if completed else "0", observed_at, observed_at if completed else None, kds_status))
            if announce:
                con.execute("INSERT INTO runner_events(detail_id,kind,created_at,quantity) VALUES(?,?,?,?)",
                            (detail_id, "ready" if completed else "new", observed_at, qty))
            created += 1
        else:
            changed = existing["source_quantity"] != qty or existing["canceled_at"] is not None
            delivered = Decimal(0) if existing["canceled_at"] else min(Decimal(existing["served_quantity"]), quantity)
            pending = quantity - delivered
            newly_finished = (kds_status is not None and kds_status in done_statuses
                              and existing["kds_status"] != kds_status
                              and quantity == Decimal(existing["source_quantity"]))
            finished_quantity = format(pending.normalize(), "f")
            if newly_finished:
                delivered = quantity
                pending = Decimal(0)
            reopened = pending > 0 and (existing["served_at"] is not None or existing["canceled_at"] is not None)
            served_at = None if pending > 0 else (observed_at if newly_finished else existing["served_at"] or observed_at)
            con.execute("""UPDATE runner_items SET item_name=?,item_key=?,quantity=?,source_quantity=?,served_quantity=?,
                canceled_at=NULL,served_at=?,first_seen_at=CASE WHEN ? THEN ? ELSE first_seen_at END,
                last_alert_at=CASE WHEN ? THEN NULL ELSE last_alert_at END,kds_status=? WHERE detail_id=?""",
                (name, item_key, format(pending.normalize(), "f"), qty, format(delivered.normalize(), "f"),
                 served_at, int(reopened), observed_at, int(reopened), kds_status, detail_id))
            if newly_finished and announce and Decimal(finished_quantity) > 0:
                con.execute("INSERT INTO runner_events(detail_id,kind,created_at,quantity) VALUES(?,'ready',?,?)",
                            (detail_id, observed_at, finished_quantity))
            elif changed and pending > 0 and announce and (existing["served_at"] is None or reopened):
                previous = Decimal(existing["source_quantity"])
                kind = "added" if quantity > previous else "reduced" if quantity < previous else "updated"
                spoken = quantity - previous if quantity > previous else pending
                con.execute("INSERT INTO runner_events(detail_id,kind,created_at,quantity) VALUES(?,?,?,?)",
                            (detail_id, kind, observed_at, format(spoken.normalize(), "f")))
    for row in con.execute("SELECT detail_id FROM runner_items WHERE order_id=? AND served_at IS NULL AND canceled_at IS NULL",
                           (order_id,)):
        if row["detail_id"] not in current_ids:
            con.execute("UPDATE runner_items SET canceled_at=? WHERE detail_id=?", (observed_at, row["detail_id"]))
    return created


def create_late_events(con, observed_at: datetime, late_minutes: int, repeat_minutes: int) -> int:
    created = 0
    for row in con.execute("""SELECT detail_id,first_seen_at,last_alert_at,quantity FROM runner_items
        WHERE served_at IS NULL AND canceled_at IS NULL"""):
        first = datetime.fromisoformat(row["first_seen_at"])
        last = datetime.fromisoformat(row["last_alert_at"]) if row["last_alert_at"] else None
        if (observed_at-first).total_seconds() < late_minutes * 60:
            continue
        if last and (observed_at-last).total_seconds() < repeat_minutes * 60:
            continue
        timestamp = _stamp(observed_at)
        con.execute("INSERT INTO runner_events(detail_id,kind,created_at,quantity) VALUES(?,'late',?,?)",
                    (row["detail_id"], timestamp, row["quantity"]))
        con.execute("UPDATE runner_items SET last_alert_at=? WHERE detail_id=?", (timestamp, row["detail_id"]))
        created += 1
    return created


def queue_snapshot(con) -> dict[str, dict]:
    rows = con.execute("""SELECT d.detail_id,d.item_name,d.item_key,d.quantity,d.source_quantity,
        o.table_name,o.order_no FROM runner_items d JOIN runner_orders o ON o.order_id=d.order_id
        WHERE d.served_at IS NULL AND d.canceled_at IS NULL""")
    return {row["detail_id"]: dict(row) for row in rows}


def emit_queue_changes(con, before: dict[str, dict], after: dict[str, dict], observed_at: str) -> None:
    """Announce one KDS completion and one current total per changed dish."""
    remaining_by_key: dict[str, list[dict]] = {}
    for row in after.values():
        key = row["item_key"] or "name:" + row["item_name"].casefold()
        remaining_by_key.setdefault(key, []).append(row)

    ready_by_key: dict[str, list[dict]] = {}
    if os.environ.get("RUNNER_COMPLETION_MODE", "runner") == "kds":
        for detail_id, old in sorted(before.items()):
            if detail_id in after:
                continue
            state = con.execute("SELECT served_at,canceled_at,kds_status FROM runner_items WHERE detail_id=?",
                                (detail_id,)).fetchone()
            if not state or not state["served_at"] or state["canceled_at"] is not None:
                continue
            if state["kds_status"] not in kds_done_statuses():
                continue
            key = old["item_key"] or "name:" + old["item_name"].casefold()
            ready_by_key.setdefault(key, []).append(old)
        for key, completed in sorted(ready_by_key.items()):
            done = sum((Decimal(row["quantity"]) for row in completed), Decimal(0))
            remaining = sum((Decimal(row["quantity"]) for row in remaining_by_key.get(key, [])), Decimal(0))
            representative = completed[0]
            con.execute("""INSERT INTO runner_events(detail_id,kind,created_at,quantity,dish_name,remaining_text)
                VALUES(?,'ready',?,?,?,?)""", (representative["detail_id"], observed_at,
                format(done.normalize(), "f"), representative["item_name"],
                "Còn " + format(remaining.normalize(), "f") + " phần"))

    additions: dict[str, Decimal] = {}
    for detail_id, row in after.items():
        old = before.get(detail_id)
        added = Decimal(row["quantity"]) if old is None else max(
            Decimal(0), Decimal(row["source_quantity"]) - Decimal(old["source_quantity"]))
        if added > 0:
            key = row["item_key"] or "name:" + row["item_name"].casefold()
            additions[key] = additions.get(key, Decimal(0)) + added
    for key in sorted(additions):
        if key in ready_by_key:
            continue
        rows = remaining_by_key[key]
        total = sum((Decimal(row["quantity"]) for row in rows), Decimal(0))
        if total <= 0:
            continue
        representative = sorted(rows, key=lambda row: row["detail_id"])[0]
        con.execute("""INSERT INTO runner_events(detail_id,kind,created_at,quantity,added_quantity,dish_name)
            VALUES(?,'total',?,?,?,?)""", (representative["detail_id"], observed_at,
            format(total.normalize(), "f"), format(additions[key].normalize(), "f"), representative["item_name"]))


def poll_once(client: Client, late_minutes: int, repeat_minutes: int) -> tuple[int, int]:
    scanned_at = datetime.now(timezone.utc)
    with app.db() as con:
        state = con.execute("SELECT last_success_at FROM runner_monitor_state WHERE id=1").fetchone()
        baseline = state is None or not state["last_success_at"]
        since = max(scanned_at-timedelta(hours=6),
                    datetime.fromisoformat(state["last_success_at"])-timedelta(minutes=2)) if state and state["last_success_at"] else scanned_at-timedelta(hours=6)
        active_ids = {row["order_id"] for row in con.execute("""SELECT DISTINCT o.order_id FROM runner_orders o
            JOIN runner_items d ON d.order_id=o.order_id WHERE d.served_at IS NULL AND d.canceled_at IS NULL""")}
        before = queue_snapshot(con)
    recent = list(client.orders_since(since))
    # Paid orders already completed before monitoring starts cannot be assumed to need service.
    # Orders tracked while active remain monitored after payment until the runner confirms delivery.
    ids = active_ids | {_safe_text(row.get("Id"), 80) for row in recent if int(row.get("Status", 0)) in NEW_ACTIVE}
    ids.discard("")
    if len(ids) > 250:
        raise CukcukError("Quá 250 order cần kiểm tra trong một lượt")
    created = 0
    for order_id in ids:
        detail = client.order_detail(order_id)
        if detail.get("BranchId") and detail["BranchId"].lower() != client.branch_id.lower():
            raise CukcukError("Order trả về sai chi nhánh")
        with app.db() as con:
            created += save_order(con, detail, _stamp(scanned_at), announce=False)
    with app.db() as con:
        after = queue_snapshot(con)
        if not baseline:
            emit_queue_changes(con, before, after, _stamp(scanned_at))
        late = create_late_events(con, scanned_at, late_minutes, repeat_minutes)
        con.execute("""INSERT INTO runner_monitor_state(id,last_success_at,last_error,updated_at)
            VALUES(1,?,NULL,?) ON CONFLICT(id) DO UPDATE SET last_success_at=excluded.last_success_at,
            last_error=NULL,updated_at=excluded.updated_at""", (_stamp(scanned_at), _stamp(scanned_at)))
    return created, late


def main():
    parser = argparse.ArgumentParser(description="Theo dõi order CUKCUK và nhắc món")
    parser.add_argument("--once", action="store_true", help="Chạy một lượt để kiểm tra kết nối")
    args = parser.parse_args()
    late_minutes = int(os.environ.get("RUNNER_LATE_MINUTES", "15"))
    repeat_minutes = int(os.environ.get("RUNNER_REPEAT_MINUTES", "5"))
    interval = int(os.environ.get("RUNNER_POLL_SECONDS", "30"))
    if not (1 <= late_minutes <= 180 and 1 <= repeat_minutes <= 60 and 5 <= interval <= 300):
        parser.error("Ngưỡng nhắc hoặc chu kỳ kiểm tra không hợp lệ")
    if os.environ.get("RUNNER_COMPLETION_MODE", "runner") == "kds" and not kds_done_statuses():
        parser.error("Chưa xác minh mã KDS; cần đặt CUKCUK_KDS_DONE_STATUSES")
    app.init_db()
    client = Client.from_environment()
    failures = 0
    while True:
        try:
            new, late = poll_once(client, late_minutes, repeat_minutes)
            failures = 0
            print(f"Đã kiểm tra order; món mới={new}; nhắc quá hạn={late}", flush=True)
        except (CukcukError, OSError, ValueError) as exc:
            failures += 1
            # Errors contain only coarse API codes, never request bodies or credentials.
            with app.db() as con:
                con.execute("""INSERT INTO runner_monitor_state(id,last_error,updated_at)
                    VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET last_error=excluded.last_error,
                    updated_at=excluded.updated_at""", (str(exc)[:200], app.now()))
            print("Lỗi theo dõi order: " + str(exc), flush=True)
            if args.once:
                raise SystemExit(1)
        if args.once:
            return
        # Wait longer after API/network errors (including CUKCUK ErrorType 102)
        # so a busy service is not retried at the normal polling rate.
        time.sleep(min(300, interval * (2 ** min(failures, 5))))


if __name__ == "__main__":
    main()
