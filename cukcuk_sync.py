"""Read-only CUKCUK invoice sync. No customer or card data is stored."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

import app

BASE_URL = "https://graphapi.cukcuk.vn"
_OPENER = build_opener(ProxyHandler({}))


class CukcukError(RuntimeError):
    pass


def request_json(path: str, payload: dict, headers: dict | None = None) -> dict:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    req = Request(BASE_URL + path, body, {"Content-Type": "application/json", **(headers or {})}, method="POST")
    try:
        with _OPENER.open(req, timeout=30) as response:
            result = json.load(response)
    except HTTPError as exc:
        if exc.code == 401:
            raise CukcukError("CUKCUK_TOKEN_EXPIRED") from exc
        raise CukcukError(f"CUKCUK HTTP {exc.code}") from exc
    if not isinstance(result, dict) or result.get("Success") is not True:
        code = result.get("ErrorType", "unknown") if isinstance(result, dict) else "invalid-response"
        raise CukcukError(f"CUKCUK ErrorType {code}")
    return result


def get_json(path: str, headers: dict) -> dict:
    req = Request(BASE_URL + path, headers=headers, method="GET")
    try:
        with _OPENER.open(req, timeout=30) as response:
            result = json.load(response)
    except HTTPError as exc:
        if exc.code == 401:
            raise CukcukError("CUKCUK_TOKEN_EXPIRED") from exc
        raise CukcukError(f"CUKCUK HTTP {exc.code}") from exc
    if not isinstance(result, dict) or result.get("Success") is not True:
        code = result.get("ErrorType", "unknown") if isinstance(result, dict) else "invalid-response"
        raise CukcukError(f"CUKCUK ErrorType {code}")
    return result


class Client:
    def __init__(self, app_id: str, domain: str, secret: str, branch_id: str, transport=request_json, get_transport=get_json):
        if not all((app_id, domain, secret)):
            raise CukcukError("Thiếu CUKCUK_APP_ID, CUKCUK_DOMAIN hoặc CUKCUK_SECRET_KEY")
        self.app_id, self.domain, self.secret, self.branch_id = app_id, domain, secret, branch_id
        self.transport = transport
        self.get_transport = get_transport
        self.token = self.company_code = None

    @classmethod
    def from_environment(cls):
        return cls(*(os.environ.get(key, "") for key in
                     ("CUKCUK_APP_ID", "CUKCUK_DOMAIN", "CUKCUK_SECRET_KEY", "CUKCUK_BRANCH_ID")))

    def login(self):
        stamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        payload = {"AppID": self.app_id, "Domain": self.domain, "LoginTime": stamp}
        signed = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        payload["SignatureInfo"] = hmac.new(self.secret.encode(), signed, hashlib.sha256).hexdigest()
        result = self.transport("/api/Account/Login", payload)["Data"]
        self.token, self.company_code = result["AccessToken"], result["CompanyCode"]

    def resolve_branch(self):
        if not self.branch_id:
            branches = self.get_transport("/api/v1/branchs/all",
                {"Authorization": "Bearer " + self.token, "CompanyCode": self.company_code}).get("Data") or []
            branches = [row for row in branches if not row.get("Inactive")]
            if len(branches) > 1:
                branches = [row for row in branches if not row.get("IsBaseDepot")]
            if len(branches) != 1:
                raise CukcukError("Không xác định được một chi nhánh duy nhất; đặt CUKCUK_BRANCH_ID")
            self.branch_id = branches[0]["Id"]

    def invoices(self, from_date: date, to_date: date):
        if from_date > to_date:
            raise ValueError("Ngày bắt đầu phải trước ngày kết thúc")
        if not self.token:
            self.login()
        self.resolve_branch()
        page = 1
        while True:
            payload = {"BranchId": self.branch_id, "FromDate": from_date.isoformat(),
                       "ToDate": to_date.isoformat(), "Page": page, "Limit": 100}
            headers = {"Authorization": "Bearer " + self.token, "CompanyCode": self.company_code}
            try:
                result = self.transport("/api/v1/sainvoices/paging-with-detail", payload, headers)
            except CukcukError as exc:
                if str(exc) != "CUKCUK_TOKEN_EXPIRED":
                    raise
                self.login()
                headers = {"Authorization": "Bearer " + self.token, "CompanyCode": self.company_code}
                result = self.transport("/api/v1/sainvoices/paging-with-detail", payload, headers)
            rows = result.get("Data") or []
            if not isinstance(rows, list):
                raise CukcukError("CUKCUK trả về danh sách hóa đơn không hợp lệ")
            yield from rows
            if page * 100 >= int(result.get("Total", 0)) or not rows:
                break
            page += 1

    def inventory_items(self):
        """Yield the CUKCUK catalog ID and Code used to classify live orders."""
        if not self.token:
            self.login()
        self.resolve_branch()
        for page in range(1, 21):
            payload = {"Page": page, "Limit": 100, "BranchId": self.branch_id,
                       "CategoryId": "", "KeySearch": "", "includeInactive": False}
            headers = {"Authorization": "Bearer " + self.token, "CompanyCode": self.company_code}
            try:
                result = self.transport("/api/v1/inventoryitems/paging", payload, headers)
            except CukcukError as exc:
                if str(exc) != "CUKCUK_TOKEN_EXPIRED":
                    raise
                self.login()
                headers = {"Authorization": "Bearer " + self.token, "CompanyCode": self.company_code}
                result = self.transport("/api/v1/inventoryitems/paging", payload, headers)
            rows = result.get("Data") or []
            if not isinstance(rows, list):
                raise CukcukError("Danh sach mat hang CUKCUK khong hop le")
            yield from rows
            if len(rows) < 100:
                return
        raise CukcukError("Qua 20 trang mat hang CUKCUK")

    def orders_since(self, last_sync: datetime):
        if not self.token:
            self.login()
        if not self.branch_id:
            self.resolve_branch()
        page = 1
        stamp = last_sync.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        while page <= 20:
            headers = {"Authorization": "Bearer " + self.token, "CompanyCode": self.company_code}
            body = {"Page": page, "Limit": 100, "BranchId": self.branch_id, "LastSyncDate": stamp}
            try:
                result = self.transport("/api/v1/orders/paging", body, headers)
            except CukcukError as exc:
                if str(exc) != "CUKCUK_TOKEN_EXPIRED":
                    raise
                self.login()
                headers = {"Authorization": "Bearer " + self.token, "CompanyCode": self.company_code}
                result = self.transport("/api/v1/orders/paging", body, headers)
            rows = result.get("Data") or []
            if not isinstance(rows, list):
                raise CukcukError("Danh sách order không hợp lệ")
            yield from rows
            if len(rows) < 100:
                return
            page += 1
        raise CukcukError("Quá 20 trang order; thu hẹp khoảng đồng bộ")

    def order_detail(self, order_id: str):
        if not re.fullmatch(r"[0-9a-fA-F-]{36}", order_id):
            raise CukcukError("Mã order không hợp lệ")
        if not self.token:
            self.login()
        headers = {"Authorization": "Bearer " + self.token, "CompanyCode": self.company_code}
        path = "/api/v1/orders/" + order_id
        try:
            result = self.get_transport(path, headers)
        except CukcukError as exc:
            if str(exc) != "CUKCUK_TOKEN_EXPIRED":
                raise
            self.login()
            headers = {"Authorization": "Bearer " + self.token, "CompanyCode": self.company_code}
            result = self.get_transport(path, headers)
        data = result.get("Data")
        if not isinstance(data, dict):
            raise CukcukError("Chi tiết order không hợp lệ")
        return data


def _num(value) -> str:
    return str(Decimal(str(value or 0)))


def store_invoices(con, invoices, branch_id: str) -> int:
    count = 0
    for invoice in invoices:
        if invoice.get("BranchId") != branch_id:
            raise CukcukError("Hóa đơn trả về sai chi nhánh")
        ref_id = invoice.get("RefId")
        if not ref_id or not invoice.get("RefDate"):
            raise CukcukError("Hóa đơn thiếu mã hoặc ngày")
        con.execute("""INSERT INTO cukcuk_invoices(ref_id,ref_no,ref_date,branch_id,payment_status,table_name,total_amount,
                     cash_amount,card_amount,modified_date) VALUES(?,?,?,?,?,?,?,?,?,?)
                     ON CONFLICT(ref_id) DO UPDATE SET ref_no=excluded.ref_no,ref_date=excluded.ref_date,
                     payment_status=excluded.payment_status,table_name=excluded.table_name,total_amount=excluded.total_amount,
                     cash_amount=excluded.cash_amount,card_amount=excluded.card_amount,
                     modified_date=excluded.modified_date""",
                     (ref_id, invoice.get("RefNo", ""), invoice["RefDate"], branch_id,
                     int(invoice.get("PaymentStatus", 0)), str(invoice.get("TableName") or ""), _num(invoice.get("TotalAmount")),
                     _num(invoice.get("CashAmount")), _num(invoice.get("CardAmount")),
                     invoice.get("ModifiedDate", "")))
        con.execute("DELETE FROM cukcuk_invoice_items WHERE ref_id=?", (ref_id,))
        con.execute("DELETE FROM cukcuk_invoice_payments WHERE ref_id=?", (ref_id,))
        for item in invoice.get("SAInvoiceDetails") or []:
            # RefDetailType=1 is the actual sellable item; extras/notes are not counted as separate sales.
            if int(item.get("RefDetailType", 0)) != 1:
                continue
            con.execute("""INSERT INTO cukcuk_invoice_items(detail_id,ref_id,item_code,item_name,quantity,amount,unit_name)
                          VALUES(?,?,?,?,?,?,?)""", (item["RefDetailId"], ref_id,
                          str(item.get("ItemCode") or "").upper(), item.get("ItemName", ""),
                          _num(item.get("Quantity")), _num(item.get("Amount")), str(item.get("UnitName") or "")))
        for payment in invoice.get("SAInvoicePayments") or []:
            con.execute("""INSERT INTO cukcuk_invoice_payments(payment_id,ref_id,payment_type,amount)
                         VALUES(?,?,?,?)""", (payment["SAInvoicePaymentID"], ref_id,
                         int(payment.get("PaymentType", 0)), _num(payment.get("Amount"))))
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Đồng bộ hóa đơn CUKCUK chỉ đọc")
    parser.add_argument("--from", dest="from_date", required=True)
    parser.add_argument("--to", dest="to_date", required=True)
    args = parser.parse_args()
    start, end = date.fromisoformat(args.from_date), date.fromisoformat(args.to_date)
    if (end - start).days > 31:
        parser.error("Mỗi lần đồng bộ tối đa 32 ngày")
    app.init_db()
    client = Client.from_environment()
    total = 0
    # Commit each page to make retries safe; importing the same invoice updates its current state.
    batch = []
    for invoice in client.invoices(start, end):
        batch.append(invoice)
        if len(batch) == 100:
            with app.db() as con:
                total += store_invoices(con, batch, client.branch_id)
            batch = []
    if batch:
        with app.db() as con:
            total += store_invoices(con, batch, client.branch_id)
    with app.db() as con:
        con.execute("INSERT INTO cukcuk_sync_runs(from_date,to_date,completed_at,invoice_count) VALUES(?,?,?,?)",
                    (start.isoformat(), end.isoformat(), app.now(), total))
    print(f"Synced {total} invoices; customer and card data were not stored.")


if __name__ == "__main__":
    main()
