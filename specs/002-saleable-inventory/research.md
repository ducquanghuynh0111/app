# Nghiên cứu dữ liệu và quyết định

## Dòng order đang mở

- **Decision**: Lấy order đang mở, đọc `OrderDetails`, dùng `ItemId` tra mã trong danh mục CUKCUK rồi ánh xạ vào nhóm kiểm kê; giữ `TableName` như nguồn trả về.
- **Rationale**: [Tài liệu Orders detail của MISA](https://graphapi.cukcuk.vn/document/api/orders_detail.html) mô tả `OrderDetails` có `ItemId`, `Quantity`, còn order có `Status` và `TableName`. Dòng chi tiết không có mã món trực tiếp trong danh sách trường công bố.
- **Alternatives considered**: Đoán nhóm bằng tên món; không chọn vì tên có thể trùng hoặc thay đổi.

## Hàng kèm bàn

- **Decision**: BATR → bánh tráng; DAUPHONG và DAPH → cùng nhóm đậu phộng. Cộng lượng hai mã để xét bàn đã có đậu phộng; giữ mã gốc khi mở chi tiết.
- **Rationale**: Chủ quán xác nhận cả ba mã và hai mã đậu phộng đều đang dùng.
- **Alternatives considered**: Chỉ chọn một mã đậu phộng; bỏ sót bàn gọi mã còn lại.

## Trả/hủy từng món

- **Decision**: Nếu dữ liệu hiện có không chứng minh được lịch sử trả/hủy theo từng dòng, hiển thị “Chưa có dữ liệu”.
- **Rationale**: [Tài liệu SAInvoice detail của MISA](https://graphapi.cukcuk.vn/document/api/sainvoices_detail.html) nêu lượng trên chi tiết hóa đơn; [Orders detail](https://graphapi.cukcuk.vn/document/api/orders_detail.html) nêu lượng hiện tại của dòng order. Tài liệu chưa xác nhận lịch sử số lượng hủy theo từng dòng. Chủ quán yêu cầu không suy đoán.
- **Alternatives considered**: Lấy chênh giữa các lượt đồng bộ làm lượng hủy; chênh đó cũng có thể do sửa số lượng hoặc chuyển bàn, nên không đủ tin cậy.

## Tải dữ liệu

- **Decision**: Lấy khi mở màn và khi người dùng yêu cầu; không thêm vòng gọi định kỳ cho CUKCUK ở giai đoạn này.
- **Rationale**: Chủ quán ưu tiên giới hạn tải; dữ liệu danh mục được lưu tạm và order chỉ được hỏi khi cần xem.
- **Alternatives considered**: Tự quét mỗi 10 phút; chưa có số liệu giới hạn API để cam kết.
