"""Compare documented CUKCUK order-detail Status codes around a KDS action.

Print only status counts. Never print orders, dish names, customer data or credentials.
"""

import os
from collections import Counter

from cukcuk_sync import Client


def status_counts(client: Client, order_id: str) -> Counter:
    order = client.order_detail(order_id)
    return Counter(str(item.get("Status", "missing")) for item in order.get("OrderDetails", [])
                   if not item.get("ParentId") and not item.get("AdditionId"))


def main() -> None:
    order_id = os.environ.get("CUKCUK_TEST_ORDER_ID", "").strip()
    if not order_id:
        raise SystemExit("Đặt CUKCUK_TEST_ORDER_ID cho một order thử rồi chạy lại.")
    client = Client.from_environment()
    client.login()
    before = status_counts(client, order_id)
    print("Trước thao tác KDS - số dòng theo mã Status:", dict(sorted(before.items())))
    input("Bấm hoàn thành/trả đúng một món trên KDS, rồi nhấn Enter tại đây...")
    after = status_counts(client, order_id)
    print("Sau thao tác KDS - số dòng theo mã Status:", dict(sorted(after.items())))
    if before == after:
        print("Không thấy thay đổi Status; API công khai có thể không phản ánh KDS.")
    else:
        print("Có thay đổi; cần thử trên order chỉ có một món và lặp lại để xác định mã hoàn thành.")


if __name__ == "__main__":
    main()
